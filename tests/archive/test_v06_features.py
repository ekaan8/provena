import os
import sqlite3
import json
import time
import numpy as np
import knowledge_graph
import auto_topology

TEST_DB = "test_knowledge.db"
knowledge_graph.DB_PATH = TEST_DB
auto_topology.DB_PATH = TEST_DB

def cleanup():
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except Exception as e:
            print(f"Error removing test DB: {e}")
            
    # Also clean up FAISS index files
    index_path = knowledge_graph._get_index_path()
    if os.path.exists(index_path):
        try:
            os.remove(index_path)
        except Exception as e:
            print(f"Error removing index: {e}")

def run_tests():
    print("🚀 Running Goldorn v0.6 Performance and FAISS Scale Tests...")
    cleanup()
    
    # Initialize DB
    knowledge_graph.init_db()
    
    # =========================================================================
    # Test 1: Batch Node Insertion and Dirty Flag Rebuilding
    # =========================================================================
    print("\n--- Test 1: Batch Node Ingestion and Dirty Rebuild Logic ---")
    
    # Ingest some nodes using add_node
    # Assert faiss_dirty becomes True
    knowledge_graph.add_node("node_a", "Epoll is a highly efficient I/O multiplexing mechanism on Linux.", "rfc", 0.90, "OS")
    knowledge_graph.add_node("node_b", "Select is a traditional I/O multiplexing mechanism.", "rfc", 0.80, "OS")
    
    assert knowledge_graph.is_faiss_dirty() == True, "Test 1 Failed: Adding nodes did not mark FAISS as dirty!"
    print("✓ Adding nodes correctly set faiss_dirty = True.")
    
    # Trigger first search - should build the index and reset dirty flag
    print("Executing query (triggers FAISS index sync)...")
    hits, paths = knowledge_graph.query("Epoll performance")
    
    assert len(hits) > 0, "Test 1 Failed: Query returned no results!"
    assert hits[0][0] == "node_a", f"Test 1 Failed: Expected node_a, got {hits[0][0]}"
    assert knowledge_graph.is_faiss_dirty() == False, "Test 1 Failed: Query did not reset faiss_dirty flag!"
    assert os.path.exists(knowledge_graph._get_index_path()) == True, "Test 1 Failed: index file not written!"
    print("✓ Query successfully triggered index sync and reset faiss_dirty = False.")
    
    # =========================================================================
    # Test 2: Scale Benchmark (1000 Nodes)
    # =========================================================================
    print("\n--- Test 2: Latency Benchmark with 1000 Nodes ---")
    
    print("Generating 1000 synthetic nodes...")
    t_start = time.time()
    
    # Add nodes directly to speed up (we use pre-calculated embeddings or encode in batches)
    # To run test fast, let's encode in batches
    sentences = [f"Fact number {i} explains that database indexing {i} improves read performance." for i in range(1000)]
    
    # Encode all at once using the sentence transformer model
    print("Encoding 1000 sentences (using sentence-transformers)...")
    embs = knowledge_graph._model.encode(sentences)
    
    print("Inserting 1000 nodes into SQLite...")
    conn = sqlite3.connect(TEST_DB)
    # We do a transaction for speed
    conn.execute("BEGIN TRANSACTION")
    for i in range(1000):
        nid = f"scale_node_{i}"
        content = sentences[i]
        emb_json = json.dumps(embs[i].tolist())
        conn.execute(
            "INSERT OR REPLACE INTO nodes (id, content, source, confidence, domain, embedding, created_at) VALUES (?,?,?,?,?,?,?)",
            (nid, content, "benchmark", 0.85, "DB", emb_json, "2026-06-24")
        )
    conn.commit()
    conn.close()
    
    # Set dirty flag manually since we bypassed add_node
    knowledge_graph.set_faiss_dirty(True)
    t_ingest = time.time() - t_start
    print(f"✓ Ingested 1000 nodes in {t_ingest:.2f} seconds.")
    
    # Let's add 500 random edges between these nodes to simulate a dense graph
    print("Inserting 500 edges to build network...")
    conn = sqlite3.connect(TEST_DB)
    conn.execute("BEGIN TRANSACTION")
    for i in range(500):
        from_n = f"scale_node_{i}"
        to_n = f"scale_node_{(i + 1) % 1000}"
        conn.execute(
            "INSERT OR REPLACE INTO edges (from_node, to_node, relation, weight, last_active) VALUES (?,?,?,?,?)",
            (from_n, to_n, "supports", 0.75, "2026-06-24")
        )
    conn.commit()
    conn.close()
    
    # Run query and measure latency
    print("Running optimized scale query...")
    t_query_start = time.time()
    hits, paths = knowledge_graph.query("database indexing read performance improvements")
    t_latency_ms = (time.time() - t_query_start) * 1000
    
    print(f"Hits: {[h[0] for h in hits]}")
    print(f"Query latency: {t_latency_ms:.2f} ms")
    
    # Assert query latency is well below 200ms
    assert t_latency_ms < 200, f"Test 2 Failed: Query latency is too high ({t_latency_ms:.2f} ms), target is < 200ms!"
    print(f"✓ Latency target achieved: {t_latency_ms:.2f} ms (Target is < 200ms, ideal < 50ms).")

    # =========================================================================
    # Test 3: Subgraph Limits
    # =========================================================================
    print("\n--- Test 3: Active Subgraph Limits Verification ---")
    
    # Test subgraph loading directly with limits
    candidate_ids = [f"scale_node_{i}" for i in range(100)] # 100 candidates
    node_map, active_edges = knowledge_graph.load_active_subgraph(candidate_ids, hops=2, max_nodes=50, max_edges=100)
    
    print(f"Active nodes size: {len(node_map)}")
    print(f"Active edges size: {len(active_edges)}")
    
    assert len(node_map) <= 50, f"Test 3 Failed: Subgraph node count {len(node_map)} exceeded limit 50!"
    assert len(active_edges) <= 100, f"Test 3 Failed: Subgraph edge count {len(active_edges)} exceeded limit 100!"
    print("✓ Active subgraph constraints successfully enforced.")
    
    print("\n🎉 All Goldorn v0.6 Scale and FAISS tests passed successfully!")
    cleanup()

if __name__ == "__main__":
    run_tests()
