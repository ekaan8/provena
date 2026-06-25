import os
import sqlite3
import json
import numpy as np
from datetime import date
import knowledge_graph
import auto_topology

# Redirect DB to test DB
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
    print("🚀 Running Goldorn v0.3 Entegrasyon Testleri...")
    cleanup()
    
    # Initialize DB
    knowledge_graph.init_db()
    
    # =========================================================================
    # Test 1: Contradiction Resolution at Query Time
    # =========================================================================
    print("\n--- Test 1: Contradiction Resolution at Query Time ---")
    
    # Ingest Statement 1 (Winner candidate - high confidence)
    statement_1 = "Epoll is highly efficient for high connection counts."
    auto_topology.ingest(statement_1, source="source_a", domain_hint="OS", confidence=0.90)
    
    # Ingest Statement 2 (Loser candidate - contradicts, gets lower confidence)
    statement_2 = "Epoll is not efficient for high connection counts."
    auto_topology.ingest(statement_2, source="source_b", domain_hint="OS", confidence=0.90)
    
    # Query the system - should trigger contradiction resolution
    print("\nExecuting query containing contradictory nodes:")
    top_node = knowledge_graph.ask("Epoll performance under high connections")
    
    # Verify that winner is statement_1 (auto_epoll_highly_efficient_high)
    assert "highly_efficient" in top_node, f"Test 1 Failed: Expected winner to be highly_efficient, got {top_node}!"
    
    # Verify that contradiction decision was logged in paths
    hits, paths = knowledge_graph.query("Epoll performance under high connections")
    contradict_logs = [p for p in paths if p["relation"] == "contradict_resolution"]
    assert len(contradict_logs) > 0, "Test 1 Failed: Contradiction resolution was not logged in query paths!"
    
    print(f"  ✓ Resolution Log: Baskılanan: {contradict_logs[0]['to']} | Kazanan: {contradict_logs[0]['from']} | Neden: {contradict_logs[0]['contribution']}")
    print("✓ Test 1 Passed: Contradiction Resolution works successfully.")

    # =========================================================================
    # Test 2: Implicit Feedback Analyzer
    # =========================================================================
    print("\n--- Test 2: Implicit Feedback Analyzer ---")
    
    # Clear and start fresh for Test 2
    cleanup()
    knowledge_graph.init_db()
    
    # 2a. Ingest seed data
    print("Ingesting initial statements...")
    text_ingest = (
        "Select is a traditional IO multiplexing method. "
        "Epoll is highly efficient for high connection counts. "
        "Epoll is the modern replacement for Select in high-load situations."
    )
    auto_topology.ingest(text_ingest, source="src", domain_hint="OS", confidence=0.90)
    
    # Manually ensure edges for consistent path routing
    knowledge_graph.add_edge("auto_epoll_modern_replacement_select", "auto_select_traditional_multiplexing_method", "supersedes", 0.80)
    knowledge_graph.add_edge("auto_epoll_highly_efficient_high", "auto_epoll_modern_replacement_select", "supports", 0.80)
    
    # Verify we have edges
    conn = sqlite3.connect(TEST_DB)
    edges_before = conn.execute("SELECT from_node, to_node, weight FROM edges").fetchall()
    print(f"Edges before implicit feedback:")
    for f, t, w in edges_before:
        print(f"  {f} -> {t} (w: {w:.3f})")
        
    # 2b. Simulate Implicit Penalty (similar queries, different top nodes)
    # Query 1
    print("\nSimulating Implicit Penalty...")
    q1 = "How to select IO multiplexing"
    knowledge_graph.ask(q1) # will log episode 1
    
    # Query 2 (very similar text, but let's change query slightly to hit another node or simulate it directly in DB)
    q2 = "How to select IO multiplexing method"
    # We will log the episode directly with a different top node to simulate user choosing/getting another node
    knowledge_graph.log_episode(q2, top_node="auto_select_traditional_method") # different node
    
    # Run analyzer
    knowledge_graph.analyze_implicit_feedback()
    
    # Verify that an implicit penalty was recorded in history
    history = conn.execute("SELECT from_node, to_node, old_weight, new_weight, reason FROM edge_history").fetchall()
    print("Edge History after Penalty:")
    for f, t, ow, nw, r in history:
        print(f"  {f} -> {t} ({ow:.3f} -> {nw:.3f}) reason: {r}")
        
    has_penalty = any(r == "implicit_penalty" for _, _, _, _, r in history)
    assert has_penalty, "Test 2 Failed: No implicit penalty was recorded!"

    # 2c. Simulate Implicit Reward (similar queries, same top node)
    print("\nSimulating Implicit Reward...")
    q3 = "Why is Epoll efficient"
    knowledge_graph.ask(q3)
    
    q4 = "Why is Epoll efficient on Linux"
    knowledge_graph.ask(q4) # both query the same top node
    
    # Run analyzer
    knowledge_graph.analyze_implicit_feedback()
    
    # Verify that an implicit reward was recorded
    history_after = conn.execute("SELECT from_node, to_node, old_weight, new_weight, reason FROM edge_history").fetchall()
    print("Edge History after Reward:")
    for f, t, ow, nw, r in history_after:
        print(f"  {f} -> {t} ({ow:.3f} -> {nw:.3f}) reason: {r}")
        
    has_reward = any(r == "implicit_reward" for _, _, _, _, r in history_after)
    assert has_reward, "Test 2 Failed: No implicit reward was recorded!"
    
    conn.close()
    print("✓ Test 2 Passed: Implicit Feedback correctly penalizes and rewards edges.")
    
    print("\n🎉 All v0.3 tests passed successfully!")

if __name__ == "__main__":
    run_tests()
