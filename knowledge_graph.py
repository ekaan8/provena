import sqlite3, json, os
from datetime import date
import numpy as np
from collections import defaultdict

DB_PATH = os.environ.get("PROVENA_DB_PATH", "knowledge.db")

try:
    from sentence_transformers import SentenceTransformer
    _model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    USE_EMBEDDINGS = True
except ImportError:
    USE_EMBEDDINGS = False

VALID_RELATIONS = {
    "supports", "contradicts", "causes", "part_of",
    "example_of", "related_to", "supersedes", "uses",
    "valid_when", "alternative_to", "depends_on"
}

RELATION_BOOST = {
    "supersedes":    ("from", 0.45),
    "contradicts":   ("from", 0.30),
    "supports":      ("to",   0.35),
    "uses":          ("to",   0.20),
    "part_of":       ("to",   0.25),
    "example_of":    ("to",   0.30),
    "causes":        ("to",   0.30),
    "related_to":    ("both", 0.15),
    "valid_when":    ("from", 0.25),
    "alternative_to":("both", 0.20),
    "depends_on":    ("to",   0.20),
}

RELATION_PENALTY = {
    "supersedes":  ("to", 0.30),
    "contradicts": ("to", 0.20),
}

RELATION_DESCRIPTIONS = {
    "supports": "evidence supports confirms validates proves justifies helps backup",
    "contradicts": "contradicts opposes conflicts violates clashes disagrees refutes opposite alternative but however",
    "causes": "causes leads to results in triggers produces creates source explanation why reason",
    "part_of": "part of component element section member division segment contains",
    "example_of": "example instance illustration case sample representative",
    "related_to": "related associated connected linked relation relative",
    "supersedes": "supersedes replaces updates upgrades newer version of obsolete",
    "uses": "uses utilizes employs applies base software framework",
    "valid_when": "valid when conditional context depending on true if",
    "alternative_to": "alternative option choice substitute replacement instead of",
    "depends_on": "depends on requires relies on prerequisite needs conditional"
}

_relation_embeddings = {}

def _get_relation_embeddings():
    global _relation_embeddings
    if not _relation_embeddings and USE_EMBEDDINGS:
        for rel, desc in RELATION_DESCRIPTIONS.items():
            _relation_embeddings[rel] = _model.encode(desc)
    return _relation_embeddings

def get_relation_attention(question):
    if not USE_EMBEDDINGS:
        return {rel: 1.0 for rel in VALID_RELATIONS}
    
    q_emb = _model.encode(question)
    rel_embs = _get_relation_embeddings()
    
    raw_sims = {}
    for rel, r_emb in rel_embs.items():
        sim = _cosine(q_emb, r_emb)
        raw_sims[rel] = max(0.0, sim)
        
    total = sum(raw_sims.values())
    if total > 0:
        max_sim = max(raw_sims.values())
        min_sim = min(raw_sims.values())
        diff = max_sim - min_sim
        
        attentions = {}
        for rel, sim in raw_sims.items():
            if diff > 1e-4:
                attentions[rel] = 0.3 + 1.2 * (sim - min_sim) / diff
            else:
                attentions[rel] = 1.0
        return attentions
    else:
        return {rel: 1.0 for rel in VALID_RELATIONS}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS nodes (
            id         TEXT PRIMARY KEY,
            content    TEXT NOT NULL,
            source     TEXT,
            confidence REAL DEFAULT 0.8,
            domain     TEXT,
            embedding  TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS edges (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            from_node   TEXT NOT NULL,
            to_node     TEXT NOT NULL,
            relation    TEXT NOT NULL,
            weight      REAL DEFAULT 0.5,
            last_active TEXT,
            FOREIGN KEY(from_node) REFERENCES nodes(id),
            FOREIGN KEY(to_node)   REFERENCES nodes(id),
            UNIQUE(from_node, to_node)
        );
        CREATE TABLE IF NOT EXISTS episodes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            query      TEXT NOT NULL,
            top_node   TEXT,
            feedback   INTEGER DEFAULT 0,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS edge_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            from_node   TEXT NOT NULL,
            to_node     TEXT NOT NULL,
            old_weight  REAL,
            new_weight  REAL,
            reason      TEXT,
            created_at  TEXT
        );
        CREATE TABLE IF NOT EXISTS metadata (
            key         TEXT PRIMARY KEY,
            value       TEXT
        );
    ''')
    try:
        conn.execute("ALTER TABLE nodes ADD COLUMN faiss_id INTEGER")
    except sqlite3.OperationalError:
        pass
        
    conn.execute("INSERT OR IGNORE INTO metadata VALUES ('faiss_dirty', '1')")
    conn.commit()
    conn.close()

def set_faiss_dirty(is_dirty=True):
    conn = sqlite3.connect(DB_PATH)
    val = "1" if is_dirty else "0"
    conn.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('faiss_dirty', ?)", (val,))
    conn.commit()
    conn.close()

def is_faiss_dirty():
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT value FROM metadata WHERE key = 'faiss_dirty'").fetchone()
    conn.close()
    if row:
        return row[0] == "1"
    return True

def _get_index_path():
    import os
    db_dir = os.path.dirname(os.path.abspath(DB_PATH))
    db_name = os.path.basename(DB_PATH)
    index_name = os.path.splitext(db_name)[0] + ".index"
    return os.path.join(db_dir, index_name)

def sync_faiss_index():
    import faiss
    import os
    
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, embedding FROM nodes WHERE embedding IS NOT NULL ORDER BY id").fetchall()
    if not rows:
        conn.close()
        return
        
    embeddings = []
    ids = []
    
    for idx, (node_id, emb_json) in enumerate(rows):
        emb = np.array(json.loads(emb_json), dtype='float32')
        embeddings.append(emb)
        ids.append(node_id)
        conn.execute("UPDATE nodes SET faiss_id = ? WHERE id = ?", (idx, node_id))
        
    conn.commit()
    conn.close()
    
    embeddings = np.array(embeddings, dtype='float32')
    faiss.normalize_L2(embeddings)
    
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    
    index_path = _get_index_path()
    faiss.write_index(index, index_path)
    set_faiss_dirty(False)

def _get_faiss_index():
    import faiss
    import os
    index_path = _get_index_path()
    if is_faiss_dirty() or not os.path.exists(index_path):
        sync_faiss_index()
    if os.path.exists(index_path):
        return faiss.read_index(index_path)
    return None

def load_active_subgraph(candidate_ids, hops=2, max_nodes=200, max_edges=500):
    if len(candidate_ids) > max_nodes:
        candidate_ids = candidate_ids[:max_nodes]
        
    active_nodes = set(candidate_ids)
    active_edges = []
    
    conn = sqlite3.connect(DB_PATH)
    current_layer = set(candidate_ids)
    
    for _ in range(hops):
        if not current_layer or len(active_nodes) >= max_nodes or len(active_edges) >= max_edges:
            break
            
        placeholders = ",".join(["?"] * len(current_layer))
        query_str = f"""
            SELECT from_node, to_node, weight, relation 
            FROM edges 
            WHERE from_node IN ({placeholders}) OR to_node IN ({placeholders})
        """
        params = list(current_layer) + list(current_layer)
        rows = conn.execute(query_str, params).fetchall()
        
        next_layer = set()
        for from_node, to_node, weight, relation in rows:
            if len(active_edges) >= max_edges:
                break
                
            edge = (from_node, to_node, weight, relation)
            if edge not in active_edges:
                active_edges.append(edge)
            
            for node_id in (from_node, to_node):
                if node_id not in active_nodes:
                    if len(active_nodes) < max_nodes:
                        active_nodes.add(node_id)
                        next_layer.add(node_id)
                        
        current_layer = next_layer
        
    if active_nodes:
        placeholders = ",".join(["?"] * len(active_nodes))
        nodes_query = f"SELECT id, content, confidence, domain, created_at, embedding FROM nodes WHERE id IN ({placeholders})"
        node_rows = conn.execute(nodes_query, list(active_nodes)).fetchall()
    else:
        node_rows = []
        
    conn.close()
    
    node_map = {}
    for row in node_rows:
        node_map[row[0]] = {
            "content": row[1],
            "confidence": row[2],
            "domain": row[3],
            "created_at": row[4],
            "embedding": row[5]
        }
        
    return node_map, active_edges

def add_node(id, content, source, confidence, domain):
    emb = json.dumps(_model.encode(content).tolist()) if USE_EMBEDDINGS else None
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO nodes (id, content, source, confidence, domain, embedding, created_at) VALUES (?,?,?,?,?,?,?)",
        (id, content, source, confidence, domain, emb, date.today().isoformat())
    )
    conn.commit(); conn.close()
    set_faiss_dirty(True)

def add_edge(from_node, to_node, relation, weight=0.5):
    assert relation in VALID_RELATIONS, f"Geçersiz relation: {relation}"
    assert 0.0 <= weight <= 1.0
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO edges (from_node,to_node,relation,weight,last_active) VALUES (?,?,?,?,?)",
        (from_node, to_node, relation, weight, date.today().isoformat())
    )
    conn.commit(); conn.close()

def _cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

def _get_all_nodes():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, content, confidence, embedding FROM nodes").fetchall()
    conn.close()
    return rows

def _get_all_edges():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT from_node, to_node, weight, relation FROM edges").fetchall()
    conn.close()
    return rows

def _base_scores(question):
    rows = _get_all_nodes()
    if not rows:
        return {}
    if USE_EMBEDDINGS:
        q_emb = _model.encode(question)
        return {
            id: _cosine(q_emb, np.array(json.loads(emb))) * conf
            for id, content, conf, emb in rows if emb
        }
    q_words = set(question.lower().split())
    return {
        id: len(q_words & set(content.lower().split())) * conf
        for id, content, conf, _ in rows
    }

def resolve_contradictions(boosted, paths):
    """
    Sorgu sonucundaki düğümler arasındaki çelişkileri çözer.
    Eğer iki düğüm arasında contradicts kenarı varsa:
      1. Confidence (güven) skoru yüksek olan kazanır.
      2. Güven eşitse, created_at tarihi yeni olan (güncel bilgi) kazanır.
      3. Tarih de eşitse, episodes tablosunda daha fazla pozitif feedback alan kazanır.
    Kaybeden düğümün skoru %10'a düşürülür (bastırılır).
    """
    if not boosted:
        return
        
    conn = sqlite3.connect(DB_PATH)
    placeholders = ",".join(["?"] * len(boosted))
    
    # Çelişki kenarlarını çek (sadece aktif düğümlerle ilgili olanlar)
    contradict_edges = conn.execute(
        f"SELECT from_node, to_node FROM edges WHERE relation='contradicts' AND (from_node IN ({placeholders}) OR to_node IN ({placeholders}))",
        list(boosted.keys()) + list(boosted.keys())
    ).fetchall()
    
    # Düğüm bilgilerini çek (sadece aktif düğümler)
    node_rows = conn.execute(
        f"SELECT id, confidence, created_at FROM nodes WHERE id IN ({placeholders})",
        list(boosted.keys())
    ).fetchall()
    node_meta = {row[0]: {"confidence": row[1], "created_at": row[2]} for row in node_rows}
    
    # Pozitif geri bildirim sayıları (sadece aktif düğümler)
    feedback_counts = defaultdict(int)
    fb_rows = conn.execute(
        f"SELECT top_node, COUNT(*) FROM episodes WHERE feedback > 0 AND top_node IN ({placeholders}) GROUP BY top_node",
        list(boosted.keys())
    ).fetchall()
    for node_id, count in fb_rows:
        feedback_counts[node_id] = count
    conn.close()
    
    suppressed = set()
    
    for from_node, to_node in contradict_edges:
        # İki düğüm de şu anki sorguda aktifse (skorları > 0)
        if from_node in boosted and to_node in boosted:
            if boosted[from_node] <= 0 or boosted[to_node] <= 0:
                continue
            if from_node in suppressed or to_node in suppressed:
                continue
                
            meta_from = node_meta.get(from_node, {"confidence": 0.5, "created_at": "1970-01-01"})
            meta_to = node_meta.get(to_node, {"confidence": 0.5, "created_at": "1970-01-01"})
            
            # Karar 1: Confidence
            if meta_from["confidence"] > meta_to["confidence"]:
                winner, loser = from_node, to_node
                reason = f"confidence ({meta_from['confidence']:.2f} > {meta_to['confidence']:.2f})"
            elif meta_from["confidence"] < meta_to["confidence"]:
                winner, loser = to_node, from_node
                reason = f"confidence ({meta_to['confidence']:.2f} > {meta_from['confidence']:.2f})"
            else:
                # Karar 2: Recency
                date_from = meta_from["created_at"] or "1970-01-01"
                date_to = meta_to["created_at"] or "1970-01-01"
                if date_from > date_to:
                    winner, loser = from_node, to_node
                    reason = f"recency ({date_from} > {date_to})"
                elif date_from < date_to:
                    winner, loser = to_node, from_node
                    reason = f"recency ({date_to} > {date_from})"
                else:
                    # Karar 3: Feedback
                    fb_from = feedback_counts.get(from_node, 0)
                    fb_to = feedback_counts.get(to_node, 0)
                    if fb_from > fb_to:
                        winner, loser = from_node, to_node
                        reason = f"positive feedback ({fb_from} > {fb_to})"
                    else:
                        winner, loser = from_node, to_node
                        reason = "default fallback"
                        
            # Kaybedenin skorunu bastır (%10)
            boosted[loser] *= 0.10
            suppressed.add(loser)
            
            # Path listesine çelişki çözüm bilgisini ekle
            paths.append({
                "from": winner,
                "to": loser,
                "relation": "contradict_resolution",
                "weight": 1.0,
                "contribution": f"winner: {winner} | reason: {reason}"
            })

def query(question, top_k=3, hops=2):
    import numpy as np
    import json
    
    # Check if we should use FAISS search (if sentence-transformers is enabled and embeddings are used)
    if not USE_EMBEDDINGS:
        base = _base_scores(question)
        if not base:
            return [], []
        active_nodes = list(base.keys())
        node_map, edges = load_active_subgraph(active_nodes, hops=hops)
    else:
        # 1. Search candidate node IDs via FAISS
        index = _get_faiss_index()
        if not index:
            return [], []
            
        q_emb = _model.encode([question])
        q_emb = np.array(q_emb, dtype='float32')
        import faiss
        faiss.normalize_L2(q_emb)
        
        # We retrieve candidates from FAISS
        k_search = max(30, top_k * 3)
        total_indexed = index.ntotal
        if total_indexed == 0:
            return [], []
        k_search = min(k_search, total_indexed)
        
        scores, faiss_indices = index.search(q_emb, k_search)
        
        # Map faiss_id back to node_id
        conn = sqlite3.connect(DB_PATH)
        candidate_ids = []
        if len(faiss_indices) > 0 and len(faiss_indices[0]) > 0:
            idx_list = [int(x) for x in faiss_indices[0] if x >= 0]
            if idx_list:
                placeholders = ",".join(["?"] * len(idx_list))
                id_rows = conn.execute(f"SELECT id FROM nodes WHERE faiss_id IN ({placeholders})", idx_list).fetchall()
                candidate_ids = [r[0] for r in id_rows]
        conn.close()
        
        if not candidate_ids:
            return [], []
            
        # 2. Load active subgraph lazy (limited to avoid unbounded scaling)
        node_map, edges = load_active_subgraph(candidate_ids, hops=hops, max_nodes=200, max_edges=500)
        
        # 3. Calculate base scores for active nodes
        base = {}
        q_emb_flat = q_emb[0]
        for nid, details in node_map.items():
            emb_json = details.get("embedding")
            conf = details.get("confidence", 0.8)
            if emb_json:
                emb = np.array(json.loads(emb_json), dtype='float32')
                sim = float(np.dot(q_emb_flat, emb) / (np.linalg.norm(q_emb_flat) * np.linalg.norm(emb) + 1e-9))
                base[nid] = sim * conf
            else:
                base[nid] = 0.0

    # Ensure all nodes in active subgraph have base scores initialized
    for nid in node_map:
        if nid not in base:
            base[nid] = 0.0
            
    # Domain isolation on active nodes
    domain_map = {nid: details["domain"] for nid, details in node_map.items()}
    
    domain_max = defaultdict(float)
    for nid, score in base.items():
        d = domain_map.get(nid, "unknown")
        if score > domain_max[d]:
            domain_max[d] = score
            
    if domain_max:
        dominant = max(domain_max, key=domain_max.get)
        for nid in base:
            if domain_map.get(nid) != dominant:
                base[nid] *= 0.25
                
    boosted = dict(base)
    paths = []
    
    relation_attentions = get_relation_attention(question)
    
    # Propagation scoring on active subgraph edges
    for _ in range(hops):
        delta = {nid: 0.0 for nid in boosted}
        
        for from_node, to_node, weight, relation in edges:
            if from_node not in boosted or to_node not in boosted:
                continue
                
            same_domain = domain_map.get(from_node) == domain_map.get(to_node)
            domain_coef = 1.0 if same_domain else 0.10
            
            direction, coef = RELATION_BOOST.get(relation, ("to", 0.15))
            attention = relation_attentions.get(relation, 1.0)
            effective_coef = coef * domain_coef * attention
            
            contribution = 0.0
            if direction == "from":
                contribution = boosted[to_node] * weight * effective_coef
                delta[from_node] += contribution
            elif direction == "to":
                contribution = boosted[from_node] * weight * effective_coef
                delta[to_node] += contribution
            else:
                c1 = boosted[to_node] * weight * effective_coef
                c2 = boosted[from_node] * weight * effective_coef
                delta[from_node] += c1
                delta[to_node]   += c2
                contribution = c1 + c2
                
            if abs(contribution) > 0.005:
                paths.append({
                    "from": from_node, "to": to_node,
                    "relation": relation, "weight": weight,
                    "contribution": round(contribution, 4)
                })
                
            # Penalty
            pen_dir, pen_coef = RELATION_PENALTY.get(relation, (None, 0))
            if pen_dir == "to":
                pen = boosted[from_node] * weight * pen_coef * domain_coef * attention
                delta[to_node] -= pen
                if pen > 0.005:
                    paths.append({
                        "from": from_node, "to": to_node,
                        "relation": f"{relation}:penalty",
                        "weight": weight,
                        "contribution": round(-pen, 4)
                    })
                    
        for nid in boosted:
            boosted[nid] += delta[nid]
            
    # Contradiction resolution on active nodes
    resolve_contradictions(boosted, paths)
    
    results = [
        (nid, node_map[nid]["content"], node_map[nid]["confidence"], score)
        for nid, score in boosted.items() if nid in node_map
    ]
    return sorted(results, key=lambda x: x[3], reverse=True)[:top_k], paths


def get_neighbors(node_id):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute('''
        SELECT e.to_node, e.relation, e.weight, n.content
        FROM edges e JOIN nodes n ON e.to_node = n.id
        WHERE e.from_node = ?
        ORDER BY e.weight DESC
    ''', (node_id,)).fetchall()
    conn.close()
    return rows

def update_weight(from_node, to_node, feedback: int, confidence: float = 0.8, reason="feedback"):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT weight, last_active FROM edges WHERE from_node=? AND to_node=?",
        (from_node, to_node)
    ).fetchone()
    if not row:
        conn.close(); return None
    old_weight, last_active = row
    days = (date.today() - date.fromisoformat(last_active)).days
    new_weight = max(0.0, min(1.0,
        old_weight + (feedback * confidence) - (0.01 * days)
    ))
    conn.execute(
        "UPDATE edges SET weight=?, last_active=? WHERE from_node=? AND to_node=?",
        (new_weight, date.today().isoformat(), from_node, to_node)
    )
    # Edge değişiklik geçmişini kaydet
    conn.execute(
        "INSERT INTO edge_history (from_node, to_node, old_weight, new_weight, reason, created_at) VALUES (?,?,?,?,?,?)",
        (from_node, to_node, old_weight, new_weight, reason, date.today().isoformat())
    )
    conn.commit(); conn.close()
    return new_weight

def blame_edge(paths, feedback=-1):
    """Credit assignment: en yüksek katkılı edge'i bul ve cezalandır/ödüllendir."""
    if not paths:
        return None
    # Penalty ve çelişki çözümleme path'lerini hariç tut
    active_paths = [p for p in paths if ":penalty" not in p["relation"] and "contradict_resolution" not in p["relation"]]
    if not active_paths:
        return None
    if feedback < 0:
        worst = max(active_paths, key=lambda p: p["contribution"])
        new_w = update_weight(worst["from"], worst["to"], feedback=-1, confidence=0.3, reason="blame")
        print(f"  ⚖️  Blamed: {worst['from']} →[{worst['relation']}]→ {worst['to']}  "
              f"katkı:{worst['contribution']:.4f}  yeni ağırlık:{new_w:.3f}")
        return worst, new_w
    elif feedback > 0:
        best = max(active_paths, key=lambda p: p["contribution"])
        new_w = update_weight(best["from"], best["to"], feedback=1, confidence=0.3, reason="reward")
        print(f"  🏆 Rewarded: {best['from']} →[{best['relation']}]→ {best['to']}  "
              f"katkı:{best['contribution']:.4f}  yeni ağırlık:{new_w:.3f}")
        return best, new_w
    return None

def analyze_implicit_feedback():
    """
    Sorgu geçmişinden (episodes) örtük (implicit) geri bildirim sinyalleri çıkarır 
    ve Hebbian kurallarıyla kenar ağırlıklarını günceller.
    """
    conn = sqlite3.connect(DB_PATH)
    # En son 20 episode'u çek
    rows = conn.execute(
        "SELECT id, query, top_node, feedback, created_at FROM episodes ORDER BY id DESC LIMIT 20"
    ).fetchall()
    conn.close()
    
    if len(rows) < 2:
        return
        
    # Kronolojik olarak sırala (eski en başta olsun)
    rows.reverse()
    
    print("\n📊 Örtük Geri Bildirim Analizi Başlatılıyor...")
    updates_count = 0
    
    # Ardışık sorgu çiftlerini incele
    for i in range(len(rows) - 1):
        id_prev, q_prev, node_prev, fb_prev, date_prev = rows[i]
        id_curr, q_curr, node_curr, fb_curr, date_curr = rows[i+1]
        
        # Sadece aynı gün yapılan sorguları incele
        if date_prev != date_curr:
            continue
            
        # Sorgu metinlerinin benzerliğini hesapla
        if USE_EMBEDDINGS:
            emb_prev = _model.encode(q_prev)
            emb_curr = _model.encode(q_curr)
            sim = _cosine(emb_prev, emb_curr)
        else:
            words_prev = set(q_prev.lower().split())
            words_curr = set(q_curr.lower().split())
            shared = words_prev & words_curr
            all_w = words_prev | words_curr
            sim = len(shared) / len(all_w) if all_w else 0.0
            
        # Eğer sorgular birbirine çok benziyorsa (> 0.80 similarity)
        if sim > 0.80:
            # Durum A: Farklı sonuçlar (Kullanıcı ilk cevabı beğenmedi, yeniden benzer arama yaptı)
            if node_prev != node_curr:
                # İlk sorgunun (q_prev) sonucunda oluşan en yüksek katkı yapan kenarı bul ve cezalandır
                _, paths = query(q_prev)
                if paths:
                    active_paths = [p for p in paths if p["relation"] != "contradict_resolution" and ":penalty" not in p["relation"]]
                    if active_paths:
                        worst = max(active_paths, key=lambda p: abs(float(p["contribution"])))
                        new_w = update_weight(worst["from"], worst["to"], feedback=-1, confidence=0.3, reason="implicit_penalty")
                        if new_w is not None:
                            print(f"  🔇 Implicit Penalty: '{q_prev}' -> '{q_curr}' (farklı node)  "
                                  f"Kenar: {worst['from']} → {worst['to']} yeni ağırlık: {new_w:.3f}")
                            updates_count += 1
            
            # Durum B: Aynı sonuçlar (Kullanıcı benzer sorguyla aynı node'a ulaştı, pekiştirme)
            else:
                _, paths = query(q_curr)
                if paths:
                    active_paths = [p for p in paths if p["relation"] != "contradict_resolution" and ":penalty" not in p["relation"]]
                    if active_paths:
                        best = max(active_paths, key=lambda p: abs(float(p["contribution"])))
                        new_w = update_weight(best["from"], best["to"], feedback=1, confidence=0.3, reason="implicit_reward")
                        if new_w is not None:
                            print(f"  🔊 Implicit Reward: '{q_prev}' -> '{q_curr}' (aynı node pekiştirme)  "
                                  f"Kenar: {best['from']} → {best['to']} yeni ağırlık: {new_w:.3f}")
                            updates_count += 1
                            
    print(f"📊 Örtük Geri Bildirim Analizi Bitti. {updates_count} adet kenar güncellendi.\n")

def show_edge_history(limit=20):
    """Edge ağırlık değişim geçmişini göster."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT from_node, to_node, old_weight, new_weight, reason, created_at "
        "FROM edge_history ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    print("\n📊 Edge Değişim Geçmişi")
    print("─" * 70)
    for f, t, ow, nw, reason, ts in rows:
        direction = "↑" if nw > ow else "↓"
        print(f"  {direction} [{ts}] {f} → {t}  {ow:.3f} → {nw:.3f}  ({reason})")

def log_episode(query_text, top_node, feedback=0):
    """Her sorguyu ve sonucunu kaydet."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO episodes (query, top_node, feedback, created_at) VALUES (?,?,?,?)",
        (query_text, top_node, feedback, date.today().isoformat())
    )
    conn.commit(); conn.close()

def show_episodes(limit=10):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT created_at, query, top_node, feedback FROM episodes ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    print("\n📖 Episode Geçmişi")
    print("─" * 60)
    for ts, q, node, fb in rows:
        fb_str = "✅" if fb > 0 else ("❌" if fb < 0 else "○")
        print(f"  {fb_str} [{ts}] {q[:45]}… → {node}")

def get_node_details(node_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT content, source, confidence FROM nodes WHERE id = ?", (node_id,)).fetchone()
    conn.close()
    if row:
        return {"content": row[0], "source": row[1], "confidence": row[2]}
    return None

def get_installed_ollama_models():
    import urllib.request
    import json
    try:
        url = "http://localhost:11434/api/tags"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode("utf-8"))
            return [model["name"] for model in data.get("models", [])]
    except Exception:
        return []

def call_ollama(prompt, model):
    import urllib.request
    import json
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        res = json.loads(response.read().decode("utf-8"))
        return res.get("response", "").strip()

def generate_template_answer(question, top_nodes, paths):
    if not top_nodes:
        return "No relevant information found to generate an answer."
    
    primary_id, primary_content, primary_conf, primary_score = top_nodes[0]
    primary_details = get_node_details(primary_id)
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
        
        details = get_node_details(other_id)
        if not details:
            continue
        
        other_content = details["content"].rstrip('.')
        other_source = details["source"]
        citation = f"[{other_id}, Source: {other_source}]"
        
        if relation == "supports":
            if direction == "incoming":
                sentences.append(f"This is supported by the fact that {other_content} {citation}.")
            else:
                sentences.append(f"This supports the observation that {other_content} {citation}.")
        elif relation == "contradicts":
            sentences.append(f"However, this conflicts with another claim stating that {other_content} {citation}.")
        elif relation == "causes":
            if direction == "outgoing":
                sentences.append(f"This causes or leads to {other_content} {citation}.")
            else:
                sentences.append(f"This is caused by the fact that {other_content} {citation}.")
        elif relation == "part_of":
            if direction == "outgoing":
                sentences.append(f"This is a component of {other_content} {citation}.")
            else:
                sentences.append(f"This consists of {other_content} {citation}.")
        elif relation == "example_of":
            if direction == "outgoing":
                sentences.append(f"This serves as an example of {other_content} {citation}.")
            else:
                sentences.append(f"A specific example of this is {other_content} {citation}.")
        elif relation == "supersedes":
            if direction == "outgoing":
                sentences.append(f"This updates and supersedes the older version stating that {other_content} {citation}.")
            else:
                sentences.append(f"Note that this has been superseded by a newer version stating that {other_content} {citation}.")
        elif relation == "uses":
            if direction == "outgoing":
                sentences.append(f"This utilizes {other_content} {citation}.")
            else:
                sentences.append(f"This is used by {other_content} {citation}.")
        elif relation == "valid_when":
            if direction == "outgoing":
                sentences.append(f"This is valid under the condition that {other_content} {citation}.")
            else:
                sentences.append(f"This provides the context where {other_content} {citation} becomes valid.")
        elif relation == "alternative_to":
            sentences.append(f"An alternative option to consider is {other_content} {citation}.")
        elif relation == "depends_on":
            if direction == "outgoing":
                sentences.append(f"This depends on {other_content} {citation}.")
            else:
                sentences.append(f"This acts as a prerequisite for {other_content} {citation}.")
        else:
            sentences.append(f"This is related to {other_content} {citation} via a '{relation}' relation.")

    for res in contradict_resolutions:
        winner = res["from"]
        loser = res["to"]
        
        seen_nodes.add(winner)
        seen_nodes.add(loser)
        
        reason = res["contribution"].split(" | reason: ")[1] if " | reason: " in res["contribution"] else res["contribution"]
        
        winner_details = get_node_details(winner)
        loser_details = get_node_details(loser)
        
        if winner_details and loser_details:
            w_cite = f"[{winner}, Source: {winner_details['source']}]"
            l_cite = f"[{loser}, Source: {loser_details['source']}]"
            sentences.append(f"A contradiction between the claim '{loser_details['content'].rstrip('.')}' {l_cite} and the preferred statement '{winner_details['content'].rstrip('.')}' {w_cite} was resolved in favor of the latter based on {reason}.")

    for node_id, content, conf, score in top_nodes[1:3]:
        if node_id not in seen_nodes:
            seen_nodes.add(node_id)
            details = get_node_details(node_id)
            if details:
                sentences.append(f"Additionally, another relevant point indicates that {content.rstrip('.')} [{node_id}, Source: {details['source']}].")
                
    return " ".join(sentences)

def generate_ollama_answer(question, top_nodes, paths, model_name=None):
    models = get_installed_ollama_models()
    if not models:
        raise RuntimeError("Ollama is not running or no models are installed.")
        
    if model_name:
        if model_name not in models:
            matched = [m for m in models if model_name in m]
            if matched:
                model = matched[0]
            else:
                model = models[0]
        else:
            model = model_name
    else:
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
        details = get_node_details(node_id)
        source = details["source"] if details else "unknown"
        context_nodes.append(f"- Node ID: {node_id}\n  Content: \"{content}\"\n  Confidence: {conf}\n  Source: {source}")
        
    for path in paths:
        if path["relation"] == "contradict_resolution" or ":penalty" in path["relation"]:
            continue
        for nid in (path["from"], path["to"]):
            if nid not in seen_nodes:
                seen_nodes.add(nid)
                details = get_node_details(nid)
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
    
    return call_ollama(prompt, model)

def ask(question, hops=2, generation_mode="hybrid"):
    print(f"\n❓ {question}  (hop={hops})")
    print("─" * 60)
    
    # İlişki dikkatlerini göster
    rel_atts = get_relation_attention(question)
    sorted_atts = sorted(rel_atts.items(), key=lambda x: x[1], reverse=True)[:3]
    print("🎯 İlişki Dikkat Ağı (Top 3):")
    for rel, val in sorted_atts:
        print(f"   {rel}: {val:.3f}")
        
    hits, paths = query(question, hops=hops)
    if not hits:
        print("Eşleşen node yok.")
        return None
        
    print("\n✍️  Natural Language Response:")
    print("─" * 40)
    
    nl_response = None
    used_mode = None
    
    if generation_mode in ("hybrid", "ollama"):
        try:
            nl_response = generate_ollama_answer(question, hits, paths)
            used_mode = "Ollama SLM"
        except Exception as e:
            if generation_mode == "ollama":
                print(f"❌ Ollama generation failed: {e}")
                nl_response = f"Error: Ollama generation failed ({e})"
            else:
                nl_response = generate_template_answer(question, hits, paths)
                used_mode = "Template Compiler (Ollama Fallback)"
    else:
        nl_response = generate_template_answer(question, hits, paths)
        used_mode = "Template Compiler"
        
    print(nl_response)
    print(f"\n[Generated via: {used_mode}]")
    print("─" * 40)
    
    for i, (node_id, content, conf, score) in enumerate(hits):
        print(f"\n{'🥇' if i==0 else '📌'} [{node_id}]  güven:{conf}  skor:{score:.3f}")
        print(f"   {content}")
        for to_id, rel, w, ncontent in get_neighbors(node_id):
            print(f"   └─ [{rel}] → {to_id}  (ağırlık:{w:.2f})")
            print(f"      {ncontent[:90]}…")
            
    # Çelişki çözümleme raporu
    contradict_logs = [p for p in paths if p["relation"] == "contradict_resolution"]
    if contradict_logs:
        print(f"\n⚖️  Çelişki Çözümleme Kararı:")
        for log in contradict_logs:
            winner = log["from"]
            loser = log["to"]
            reason = log["contribution"].split(" | reason: ")[1] if " | reason: " in log["contribution"] else log["contribution"]
            print(f"   Baskılanan: [{loser}] ──> Kazanan: [{winner}] ({reason})")
            
    # Standart en etkili edge'ler (çelişki çözümlerini filtrele)
    active_paths = [p for p in paths if p["relation"] != "contradict_resolution"]
    if active_paths:
        top_paths = sorted(active_paths, key=lambda p: abs(float(p["contribution"])), reverse=True)[:5]
        print(f"\n🔗 En etkili edge'ler:")
        for p in top_paths:
            sign = "+" if float(p["contribution"]) > 0 else ""
            print(f"   {p['from']} →[{p['relation']}]→ {p['to']}  "
                  f"katkı:{sign}{p['contribution']:.4f}")
    top = hits[0][0]
    log_episode(question, top)
    return top

# Auto-initialize database on import to ensure schemas are kept in sync
init_db()