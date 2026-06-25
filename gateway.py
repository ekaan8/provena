#!/usr/bin/env python3
import sys
import os
import json
import urllib.request
import urllib.parse
import argparse

import knowledge_graph

class Gateway:
    def __init__(self, server_urls=None):
        self.server_urls = server_urls if server_urls else ["http://localhost:8001", "http://localhost:8002"]
        self.profiles = {} # url -> {"domain": ..., "embedding": ...}
        
    def discover_profiles(self):
        """Query /info on all registered servers and fetch domain profiles."""
        for url in self.server_urls:
            try:
                info_url = f"{url.rstrip('/')}/info"
                req = urllib.request.Request(info_url, method="GET")
                with urllib.request.urlopen(req, timeout=2) as response:
                    info = json.loads(response.read().decode("utf-8"))
                    domain = info.get("domain", "unknown")
                    
                    # Generate embedding for the domain name locally if embeddings are supported
                    emb = None
                    if knowledge_graph.USE_EMBEDDINGS and knowledge_graph._model:
                        emb = knowledge_graph._model.encode(domain)
                        
                    self.profiles[url] = {
                        "domain": domain,
                        "embedding": emb,
                        "total_nodes": info.get("total_nodes", 0),
                        "total_edges": info.get("total_edges", 0)
                    }
            except Exception as e:
                # If server is offline, skip it or mark it offline
                pass
                
    def _cosine_similarity(self, v1, v2):
        import numpy as np
        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def select_targets(self, question):
        """Select targets based on semantic routing similarity between query and domain names."""
        if not self.profiles:
            self.discover_profiles()
            
        if not self.profiles:
            # No online servers discovered yet, return all as fallback
            return self.server_urls
            
        q_emb = None
        if knowledge_graph.USE_EMBEDDINGS and knowledge_graph._model:
            q_emb = knowledge_graph._model.encode(question)
            
        if q_emb is None:
            # Fallback to broadcast if embeddings are disabled
            print(f"[Gateway] Broadcast Fallback (Embeddings disabled)")
            return list(self.profiles.keys())
            
        targets = []
        scores = []
        for url, profile in self.profiles.items():
            if profile["embedding"] is not None:
                sim = self._cosine_similarity(q_emb, profile["embedding"])
                scores.append((url, profile["domain"], sim))
                if sim >= 0.30: # Semantic routing threshold
                    targets.append(url)
                    
        # Log routing details to stdout
        for url, domain, sim in scores:
            route_status = "ROUTED" if url in targets else "SKIPPED"
            print(f"[Gateway Yönlendirme] Sunucu: {url} | Alan: {domain:<15} | Sim: {sim:.4f} | Karar: {route_status}")
            
        if not targets:
            # If no servers pass threshold, fallback to broadcast all
            print(f"[Gateway] Broadcast Fallback (No server met threshold 0.30)")
            return list(self.profiles.keys())
            
        return targets

    def query(self, question, top_k=5, hops=2):
        """Query target servers, merge results, resolve contradictions, and return merged hits and paths."""
        targets = self.select_targets(question)
        
        merged_hits = {}
        merged_paths = []
        merged_details = {}
        
        for url in targets:
            try:
                query_url = f"{url.rstrip('/')}/query"
                payload = {
                    "question": question,
                    "top_k": top_k,
                    "hops": hops
                }
                req = urllib.request.Request(
                    query_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    res = json.loads(response.read().decode("utf-8"))
                    
                    # Merge Hits (keep highest score if duplicate exists)
                    for hit in res.get("hits", []):
                        nid = hit["id"]
                        if nid not in merged_hits or hit["score"] > merged_hits[nid]["score"]:
                            merged_hits[nid] = hit
                            
                    # Merge Paths
                    for path in res.get("paths", []):
                        if path not in merged_paths:
                            merged_paths.append(path)
                            
                    # Merge Node Details
                    merged_details.update(res.get("node_details", {}))
            except Exception as e:
                print(f"[Gateway Hata] Sunucu sorgusu başarısız: {url} -> {e}")
                
        # Resolve contradictions across merged hits and paths
        self.resolve_contradictions_gateway(merged_hits, merged_paths)
        
        # Sort merged hits by final scores
        sorted_hits = sorted(
            [(h["id"], h["content"], h["confidence"], h["score"]) for h in merged_hits.values()],
            key=lambda x: x[3],
            reverse=True
        )[:top_k]
        
        return sorted_hits, merged_paths, merged_details

    def resolve_contradictions_gateway(self, hits_dict, paths):
        """Resolve contradictions between merged nodes from different servers without direct DB access."""
        # Find contradicts edges
        contradict_edges = []
        for p in paths:
            if p.get("relation") == "contradicts":
                contradict_edges.append((p["from"], p["to"]))
                
        suppressed = set()
        for from_node, to_node in contradict_edges:
            if from_node in hits_dict and to_node in hits_dict:
                if hits_dict[from_node]["score"] <= 0 or hits_dict[to_node]["score"] <= 0:
                    continue
                if from_node in suppressed or to_node in suppressed:
                    continue
                    
                conf_from = hits_dict[from_node].get("confidence", 0.5)
                conf_to = hits_dict[to_node].get("confidence", 0.5)
                
                # Check timestamps or other attributes if same confidence
                if conf_from > conf_to:
                    winner, loser = from_node, to_node
                    reason = f"confidence ({conf_from:.2f} > {conf_to:.2f})"
                elif conf_from < conf_to:
                    winner, loser = to_node, from_node
                    reason = f"confidence ({conf_to:.2f} > {conf_from:.2f})"
                else:
                    winner, loser = from_node, to_node
                    reason = "default fallback (equal confidence)"
                    
                # Suppress the loser score
                hits_dict[loser]["score"] *= 0.10
                suppressed.add(loser)
                
                paths.append({
                    "from": winner,
                    "to": loser,
                    "relation": "contradict_resolution",
                    "weight": 1.0,
                    "contribution": f"winner: {winner} | reason: {reason}"
                })

    def generate_template_answer(self, question, top_nodes, paths, node_details):
        if not top_nodes:
            return "No relevant information found to generate an answer."
        
        primary_id, primary_content, primary_conf, primary_score = top_nodes[0]
        primary_details = node_details.get(primary_id)
        primary_source = primary_details["source"] if primary_details else "unknown"
        
        sentences = []
        sentences.append(f"Regarding the query '{question}', the primary finding is that {primary_content.rstrip('.')} [{primary_id}, Source: {primary_source}].")
        
        connections = []
        seen_nodes = {primary_id}
        
        contradict_resolutions = []
        top_ids = {h[0] for h in top_nodes}
        for path in paths:
            if path["relation"] == "contradict_resolution":
                if path["from"] in top_ids or path["to"] in top_ids:
                    contradict_resolutions.append(path)
                    
        for path in paths:
            if path["relation"] == "contradict_resolution" or ":penalty" in path["relation"]:
                continue
            
            if path["from"] == primary_id:
                other_id = path["to"]
                direction = "outgoing"
                relation = path["relation"]
                connections.append((other_id, direction, relation, path["weight"]))
            elif path["to"] == primary_id:
                other_id = path["from"]
                direction = "incoming"
                relation = path["relation"]
                connections.append((other_id, direction, relation, path["weight"]))
                
        for other_id, direction, relation, weight in connections:
            if other_id in seen_nodes:
                continue
            seen_nodes.add(other_id)
            
            details = node_details.get(other_id)
            if not details:
                continue
            
            other_content = details["content"].rstrip('.')
            other_source = details["source"]
            citation = f"[{other_id}, Source: {other_source}]"
            
            if relation == "supports":
                if direction == "incoming":
                    sentences.append(f"This is supported by the fact that {other_content} {citation}.")
                else:
                    sentences.append(f"This supports the finding that {other_content} {citation}.")
            elif relation == "contradicts":
                sentences.append(f"However, this conflicts with another claim stating that {other_content} {citation}.")
            elif relation == "causes":
                if direction == "incoming":
                    sentences.append(f"This is caused by the fact that {other_content} {citation}.")
                else:
                    sentences.append(f"This causes {other_content} {citation}.")
            elif relation == "part_of":
                if direction == "incoming":
                    sentences.append(f"This includes {other_content} {citation} as a part.")
                else:
                    sentences.append(f"This is part of {other_content} {citation}.")
            elif relation == "example_of":
                if direction == "incoming":
                    sentences.append(f"An example of this is {other_content} {citation}.")
                else:
                    sentences.append(f"This is an example of {other_content} {citation}.")
            elif relation == "supersedes":
                if direction == "incoming":
                    sentences.append(f"This updates and supersedes the older version stating that {other_content} {citation}.")
                else:
                    sentences.append(f"This is superseded by {other_content} {citation}.")
            elif relation == "uses":
                if direction == "incoming":
                    sentences.append(f"This is utilized by {other_content} {citation}.")
                else:
                    sentences.append(f"This utilizes {other_content} {citation}.")
            elif relation == "alternative_to":
                sentences.append(f"An alternative option to consider is {other_content} {citation}.")
            elif relation == "depends_on":
                if direction == "incoming":
                    sentences.append(f"This is a dependency for {other_content} {citation}.")
                else:
                    sentences.append(f"This depends on {other_content} {citation}.")
            else:
                sentences.append(f"Additionally, another relevant point indicates that {other_content} {citation}.")
                
        for res in contradict_resolutions:
            w_details = node_details.get(res["from"])
            l_details = node_details.get(res["to"])
            if w_details and l_details:
                reason_str = res["contribution"].split(" | reason: ")[1] if " | reason: " in res["contribution"] else res["contribution"]
                sentences.append(f"A contradiction between the claim '{l_details['content'].rstrip('.')}' [{res['to']}, Source: {l_details['source']}] "
                                 f"and the preferred statement '{w_details['content'].rstrip('.')}' [{res['from']}, Source: {w_details['source']}] "
                                 f"was resolved in favor of the latter based on {reason_str}.")
                                 
        return " ".join(sentences)

    def generate_ollama_answer(self, question, top_nodes, paths, node_details):
        models = knowledge_graph.get_installed_ollama_models()
        if not models:
            raise RuntimeError("Ollama is not running or no models are installed.")
            
        preferred = ["gemma:2b", "gemma", "phi3:mini", "phi3", "llama3", "gemma2:2b"]
        model = models[0]
        for p in preferred:
            found = False
            for m in models:
                if m.startswith(p):
                    model = m
                    found = True
                    break
            if found:
                break
                
        context_nodes = []
        seen_nodes = set()
        for node_id, content, conf, score in top_nodes:
            seen_nodes.add(node_id)
            details = node_details.get(node_id)
            source = details["source"] if details else "unknown"
            context_nodes.append(f"- Node ID: {node_id}\n  Content: \"{content}\"\n  Confidence: {conf}\n  Source: {source}")
            
        for path in paths:
            if path["relation"] == "contradict_resolution" or ":penalty" in path["relation"]:
                continue
            for nid in (path["from"], path["to"]):
                if nid not in seen_nodes:
                    seen_nodes.add(nid)
                    details = node_details.get(nid)
                    if details:
                        context_nodes.append(f"- Node ID: {nid}\n  Content: \"{details['content']}\"\n  Confidence: {details['confidence']}\n  Source: {details['source']}")
                        
        context_relations = []
        for path in paths:
            if path["relation"] == "contradict_resolution":
                context_relations.append(f"- Contradiction Resolved: Winner: {path['from']}, Loser: {path['to']}, Reason: {path['contribution']}")
            elif ":penalty" in path["relation"]:
                continue
            else:
                context_relations.append(f"- {path['from']} --[{path['relation']}]--> {path['to']} (weight: {path['weight']})")
                
        nodes_str = "\n".join(context_nodes)
        relations_str = "\n".join(context_relations)
        
        prompt = f"""You are Provena's Language Generation Layer. Synthesize a coherent, fluent answer in English to the question based ONLY on the retrieved facts and their relationships provided below.

Question: {question}

Retrieved Facts:
{nodes_str}

Relationships:
{relations_str}

Instructions:
1. Write a direct, clear, and fluent answer in English.
2. You MUST use inline citations using the exact Node ID in square brackets, e.g. [auto_epoll_highly_efficient_high]. Do NOT create new Node IDs, use only the ones provided.
3. If there is a contradiction resolved, mention it and explain which claim was preferred and why.
4. Rely ONLY on the facts provided. Do not use external knowledge.

Answer:"""
        return knowledge_graph.call_ollama(prompt, model)

    def ask(self, question, hops=2, mode="hybrid"):
        """Central client interface to query across multiple domain servers and print synthetic output."""
        print(f"\n❓ {question}  (Dağıtık Gateway - hop={hops})")
        print("─" * 60)
        
        hits, paths, node_details = self.query(question, hops=hops)
        
        nl_response = ""
        used_mode = "Template Compiler (Ollama Fallback)"
        
        if mode in ("hybrid", "ollama"):
            try:
                nl_response = self.generate_ollama_answer(question, hits, paths, node_details)
                used_mode = "Ollama SLM"
            except Exception as e:
                if mode == "ollama":
                    print(f"❌ Ollama generation failed: {e}")
                    nl_response = f"Error: Ollama generation failed ({e})"
                    used_mode = "None"
                else:
                    nl_response = self.generate_template_answer(question, hits, paths, node_details)
        else:
            nl_response = self.generate_template_answer(question, hits, paths, node_details)
            used_mode = "Template Compiler"
            
        print("\n✍️  Natural Language Response:")
        print("─" * 40)
        print(nl_response)
        print(f"\n[Generated via: {used_mode}]")
        print("─" * 40)
        
        if hits:
            print(f"\n🥇 [{hits[0][0]}]  güven:{hits[0][2]}  skor:{hits[0][3]:.3f}")
            print(f"   {hits[0][1]}")
            
            for h in hits[1:]:
                print(f"\n📌 [{h[0]}]  güven:{h[2]}  skor:{h[3]:.3f}")
                print(f"   {h[1]}")
                
        # Print contradiction resolution decision
        resolutions = [p for p in paths if p["relation"] == "contradict_resolution"]
        if resolutions:
            print(f"\n⚖️  Çelişki Çözümleme Kararı:")
            for r in resolutions:
                reason = r["contribution"].split(" | reason: ")[1] if " | reason: " in r["contribution"] else r["contribution"]
                print(f"   Baskılanan: [{r['to']}] ──> Kazanan: [{r['from']}] ({reason})")
                
        # Print top paths
        active_paths = [p for p in paths if p["relation"] != "contradict_resolution"]
        if active_paths:
            top_paths = sorted(active_paths, key=lambda p: abs(float(p["contribution"])), reverse=True)[:5]
            print(f"\n🔗 En etkili edge'ler:")
            for p in top_paths:
                sign = "+" if float(p["contribution"]) > 0 else ""
                print(f"   {p['from']} →[{p['relation']}]→ {p['to']}  katkı:{sign}{p['contribution']:.4f}")
                
        return hits, paths

def main():
    parser = argparse.ArgumentParser(description="Provena Query Router (Gateway) CLI")
    parser.add_argument("question", help="The question to route and query")
    parser.add_argument("--servers", nargs="+", help="Space-separated list of server URLs")
    parser.add_argument("--hops", type=int, default=2, help="Graph hops")
    parser.add_argument("--mode", default="hybrid", choices=["hybrid", "template", "ollama"])
    args = parser.parse_args()
    
    servers = args.servers if args.servers else ["http://localhost:8001", "http://localhost:8002"]
    gateway = Gateway(servers)
    gateway.ask(args.question, hops=args.hops, mode=args.mode)

if __name__ == "__main__":
    main()
