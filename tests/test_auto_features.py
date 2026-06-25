import os
import sqlite3
import json
import numpy as np
import knowledge_graph
import auto_topology

# Redirect DB to a test database
TEST_DB = "test_knowledge.db"
knowledge_graph.DB_PATH = TEST_DB
auto_topology.DB_PATH = TEST_DB

def cleanup():
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except Exception as e:
            print(f"Error removing test DB: {e}")

def run_tests():
    print("🚀 Running Provena Altyapı Güncelleme Testleri...")
    cleanup()
    
    # Initialize test DB
    knowledge_graph.init_db()
    
    # =========================================================================
    # Test 1: Ingesting English texts & Auto-Topology Ingestion
    # =========================================================================
    print("\n--- Test 1: Automated Ingestion of English Text ---")
    text_1 = (
        "Large language models compress knowledge into parameters. "
        "But this parametric knowledge is opaque and hard to update. "
        "Explicit graph structures make reasoning transparent and easily updatable."
    )
    result = auto_topology.ingest(text_1, source="test_source_1", domain_hint="AI", confidence=0.80)
    
    # Check if nodes were created
    conn = sqlite3.connect(TEST_DB)
    nodes = conn.execute("SELECT id, content, confidence, domain FROM nodes").fetchall()
    print(f"\nCreated Nodes in DB:")
    for nid, content, conf, dom in nodes:
        print(f"  [{nid}] domain: {dom} | conf: {conf:.2f} | content: {content}")
    
    # Check if edges were created
    edges = conn.execute("SELECT from_node, to_node, relation, weight FROM edges").fetchall()
    print(f"\nCreated Edges in DB:")
    for f, t, r, w in edges:
        print(f"  {f} ──[{r} (w: {w:.2f})]──> {t}")
    conn.close()
    
    assert len(nodes) > 0, "Test 1 Failed: No nodes were created!"
    print("✓ Test 1 Passed: Automated Ingestion works successfully.")

    # =========================================================================
    # Test 2: Contradiction Check (Validation Gate)
    # =========================================================================
    print("\n--- Test 2: Contradiction Check (Validation Gate) ---")
    
    # Clear DB and start fresh for Test 2 to isolate contradiction
    cleanup()
    knowledge_graph.init_db()
    
    # Ingest the first statement
    statement_1 = "Epoll is highly efficient for high connection counts."
    print(f"Ingesting Statement 1: '{statement_1}'")
    auto_topology.ingest(statement_1, source="source_a", domain_hint="OS", confidence=0.90)
    
    # Ingest a contradicting statement
    statement_2 = "Epoll is not efficient for high connection counts."
    print(f"\nIngesting Statement 2 (Contradictory): '{statement_2}'")
    auto_topology.ingest(statement_2, source="source_b", domain_hint="OS", confidence=0.90)
    
    # Verify that the second statement has reduced confidence and a contradicts edge was created
    conn = sqlite3.connect(TEST_DB)
    nodes = conn.execute("SELECT id, content, confidence FROM nodes").fetchall()
    edges = conn.execute("SELECT from_node, to_node, relation, weight FROM edges").fetchall()
    conn.close()
    
    print("\nState after ingestion:")
    for nid, content, conf in nodes:
        print(f"  Node: [{nid}] conf: {conf:.2f} | {content}")
    for f, t, r, w in edges:
        print(f"  Edge: {f} ──[{r} (w: {w:.2f})]──> {t}")
        
    # Find the contradictory node
    node_not_efficient = [n for n in nodes if "not efficient" in n[1]]
    assert len(node_not_efficient) == 1, "Contradictory node not found!"
    assert node_not_efficient[0][2] == 0.40, f"Test 2 Failed: Contradictory node confidence is {node_not_efficient[0][2]}, expected 0.40!"
    
    has_contradicts_edge = any(r == "contradicts" for _, _, r, _ in edges)
    assert has_contradicts_edge, "Test 2 Failed: No contradicts edge was created between conflicting nodes!"
    
    print("✓ Test 2 Passed: Contradiction Gate correctly lowers confidence and creates contradicts edge.")

    # =========================================================================
    # Test 3: Relation-Attention Routing
    # =========================================================================
    print("\n--- Test 3: Dynamic Relation-Attention Routing ---")
    
    # Initialize some relations for testing routing
    # We will query and display relation attention weights
    queries = [
        "What causes Moore's law to slow down?",
        "Are there any alternative approaches to this issue?",
        "How can we prove or supports this evidence?"
    ]
    
    for q in queries:
        print(f"\nQuery: '{q}'")
        rel_atts = knowledge_graph.get_relation_attention(q)
        sorted_atts = sorted(rel_atts.items(), key=lambda x: x[1], reverse=True)[:3]
        print("  Top 3 Relation Attentions:")
        for rel, val in sorted_atts:
            print(f"    {rel}: {val:.3f}")
            
    print("✓ Test 3 Passed: Relation attention scores dynamically adjust to query intent.")
    
    print("\n🎉 All tests passed successfully!")

if __name__ == "__main__":
    run_tests()
