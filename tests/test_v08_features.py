#!/usr/bin/env python3
import os
import sqlite3
import subprocess
import time
import json
import urllib.request
import unittest

DB_OS = "test_db_os.db"
DB_CHIP = "test_db_chip.db"

def cleanup():
    for db in (DB_OS, DB_CHIP):
        if os.path.exists(db):
            try:
                os.remove(db)
            except Exception as e:
                print(f"Error removing {db}: {e}")
                
        index_file = db.replace(".db", ".index")
        if os.path.exists(index_file):
            try:
                os.remove(index_file)
            except Exception as e:
                print(f"Error removing {index_file}: {e}")
                
    for log in ("test_server_9091.log", "test_server_9092.log"):
        if os.path.exists(log):
            try:
                os.remove(log)
            except Exception as e:
                print(f"Error removing {log}: {e}")


def run_tests():
    print("🚀 Running Provena v0.8 Distributed Architecture Integration Tests...")
    cleanup()
    
    # 1. Initialize and populate OS Database
    print("\nInitializing test_db_os.db...")
    os.environ["PROVENA_DB_PATH"] = DB_OS
    import knowledge_graph
    # Re-import or force update module-level path
    knowledge_graph.DB_PATH = DB_OS
    knowledge_graph.init_db()
    
    knowledge_graph.add_node(
        "auto_epoll_highly_efficient_high",
        "Epoll is highly efficient for high connection counts.",
        "guide.pdf",
        0.90,
        "Operating Systems"
    )
    knowledge_graph.add_node(
        "auto_select_traditional_multiplexing_method",
        "Select is a traditional IO multiplexing method.",
        "rfc.txt",
        0.85,
        "Operating Systems"
    )
    knowledge_graph.add_edge(
        "auto_epoll_highly_efficient_high",
        "auto_select_traditional_multiplexing_method",
        "alternative_to",
        0.80
    )
    
    # Add a contradicts relation node for later contradiction testing
    knowledge_graph.add_node(
        "auto_epoll_inefficient",
        "Epoll is not efficient for high connection counts.",
        "guide_v2.pdf",
        0.40,
        "Operating Systems"
    )
    knowledge_graph.add_edge(
        "auto_epoll_inefficient",
        "auto_epoll_highly_efficient_high",
        "contradicts",
        0.75
    )
    
    # Force FAISS index synchronization
    knowledge_graph.sync_faiss_index()
    
    # 2. Initialize and populate Chip Database
    print("Initializing test_db_chip.db...")
    os.environ["PROVENA_DB_PATH"] = DB_CHIP
    # Force reload knowledge_graph path variable
    knowledge_graph.DB_PATH = DB_CHIP
    knowledge_graph.init_db()
    
    knowledge_graph.add_node(
        "arm_risc_architecture",
        "ARM is a RISC architecture with low transistor count.",
        "chip_design.txt",
        0.95,
        "Computer Architecture"
    )
    knowledge_graph.add_node(
        "arm_power_efficiency",
        "ARM architecture offers higher performance-per-watt efficiency.",
        "anandtech.txt",
        1.0,
        "Computer Architecture"
    )
    knowledge_graph.add_edge(
        "arm_risc_architecture",
        "arm_power_efficiency",
        "causes",
        0.90
    )
    knowledge_graph.sync_faiss_index()
    
    # 3. Start Domain Servers as Subprocesses
    print("\nStarting domain servers on ports 9091 and 9092...")
    
    # Use python executable from venv
    python_bin = "./venv/bin/python3"
    
    # Redirect server stdout/stderr to files for debugging
    f_os = open("test_server_9091.log", "w")
    f_chip = open("test_server_9092.log", "w")
    
    proc_os = subprocess.Popen(
        [python_bin, "domain_server.py", "--port", "9091", "--db", DB_OS],
        stdout=f_os,
        stderr=f_os
    )
    
    proc_chip = subprocess.Popen(
        [python_bin, "domain_server.py", "--port", "9092", "--db", DB_CHIP],
        stdout=f_chip,
        stderr=f_chip
    )
    
    # Wait dynamically for the servers to bind and start serving requests
    print("Waiting for domain servers to start and bind...")
    for port, proc, log_file, f_handle in [(9091, proc_os, "test_server_9091.log", f_os), (9092, proc_chip, "test_server_9092.log", f_chip)]:
        start_time = time.time()
        online = False
        while time.time() - start_time < 45:
            # Check if process crashed/exited early
            if proc.poll() is not None:
                f_handle.flush()
                with open(log_file, "r") as lf:
                    print(f"\n--- Port {port} Server Log Output ---")
                    print(lf.read())
                raise RuntimeError(f"Server on port {port} exited early with code {proc.returncode}")
            try:
                req = urllib.request.Request(f"http://127.0.0.1:{port}/info", method="GET")
                with urllib.request.urlopen(req, timeout=1) as response:
                    if response.status == 200:
                        online = True
                        break
            except Exception as e:
                # Print the exception to stdout for debugging
                print(f"Port {port} check failed: {type(e).__name__}: {e}")
                time.sleep(0.5)
        if not online:
            f_handle.flush()
            with open(log_file, "r") as lf:
                print(f"\n--- Port {port} Server Log Output (Timeout) ---")
                print(lf.read())
            raise RuntimeError(f"Server on port {port} failed to start within 45 seconds")
            
        f_handle.close()

            
    try:
        import gateway
        # Initialize Gateway
        gw = gateway.Gateway(["http://127.0.0.1:9091", "http://127.0.0.1:9092"])
        
        # Discover profiles
        print("Discovering profiles at Gateway...")
        gw.discover_profiles()
        assert "http://127.0.0.1:9091" in gw.profiles, "Gateway failed to discover Server 1"
        assert "http://127.0.0.1:9092" in gw.profiles, "Gateway failed to discover Server 2"
        
        print(f"Server 1 (OS) Profile: {gw.profiles['http://127.0.0.1:9091']}")
        print(f"Server 2 (Chip) Profile: {gw.profiles['http://127.0.0.1:9092']}")
        
        # =====================================================================
        # TEST 1: Semantic Yönlendirme (Routing) OS Query
        # =====================================================================
        print("\n--- Test 1: OS Query Routing ---")
        q1 = "Why is Epoll efficient?"
        targets1 = gw.select_targets(q1)
        print(f"Selected target servers for OS query: {targets1}")
        # It should route to port 9091 (OS) and NOT port 9092 (Chip)
        assert "http://127.0.0.1:9091" in targets1, "Failed to route to OS server"
        assert "http://127.0.0.1:9092" not in targets1 or len(targets1) == 2, "Routed to Chip server unnecessarily"
        
        hits1, paths1, details1 = gw.query(q1)
        print(f"Hits: {[h[0] for h in hits1]}")
        assert any("epoll" in h[0] for h in hits1), "OS query hits are missing epoll nodes"
        
        # =====================================================================
        # TEST 2: Semantic Yönlendirme (Routing) Chip Query
        # =====================================================================
        print("\n--- Test 2: Chip Query Routing ---")
        q2 = "What makes ARM power efficient?"
        targets2 = gw.select_targets(q2)
        print(f"Selected target servers for Chip query: {targets2}")
        # It should route to port 9092 (Chip) and NOT port 9091 (OS)
        assert "http://127.0.0.1:9092" in targets2, "Failed to route to Chip server"
        assert "http://127.0.0.1:9091" not in targets2 or len(targets2) == 2, "Routed to OS server unnecessarily"
        
        hits2, paths2, details2 = gw.query(q2)
        print(f"Hits: {[h[0] for h in hits2]}")
        assert any("arm" in h[0] for h in hits2), "Chip query hits are missing arm nodes"
        
        # =====================================================================
        # TEST 3: Broadcast Fallback (Cross-domain query)
        # =====================================================================
        print("\n--- Test 3: Broadcast Fallback and Results Merging ---")
        q3 = "Comparison of Epoll multiplexing and ARM architecture efficiency"
        # This cross-domain query should trigger broadcast or hit both
        hits3, paths3, details3 = gw.query(q3)
        hit_ids = [h[0] for h in hits3]
        print(f"Merged Hits: {hit_ids}")
        assert any("epoll" in hid for hid in hit_ids), "Merged hits missing OS node"
        assert any("arm" in hid for hid in hit_ids), "Merged hits missing Chip node"
        
        # =====================================================================
        # TEST 4: Cross-Domain Contradiction Resolution
        # =====================================================================
        print("\n--- Test 4: Cross-Domain Contradiction Resolution ---")
        q4 = "Epoll efficiency contradiction"
        hits4, paths4, details4 = gw.query(q4)
        
        # Check that both contradictory nodes are fetched
        hit_ids_4 = [h[0] for h in hits4]
        print(f"Hits: {hit_ids_4}")
        assert "auto_epoll_highly_efficient_high" in hit_ids_4
        assert "auto_epoll_inefficient" in hit_ids_4
        
        # Verify loser (auto_epoll_inefficient) was suppressed
        dict_hits = {h[0]: h for h in hits4}
        high_score = dict_hits["auto_epoll_highly_efficient_high"][3]
        low_score = dict_hits["auto_epoll_inefficient"][3]
        print(f"Epoll high confidence score: {high_score:.4f}")
        print(f"Epoll low confidence score (suppressed): {low_score:.4f}")
        assert high_score > low_score, "Suppressed contradictory node should have lower score"
        
        # Verify resolution logged in paths
        resolutions = [p for p in paths4 if p["relation"] == "contradict_resolution"]
        assert len(resolutions) > 0, "Contradiction resolution was not logged"
        print(f"Logged resolution: Winner = {resolutions[0]['from']}, Loser = {resolutions[0]['to']}, Reason = {resolutions[0]['contribution']}")
        assert resolutions[0]["from"] == "auto_epoll_highly_efficient_high", "Wrong winner resolved"
        assert resolutions[0]["to"] == "auto_epoll_inefficient", "Wrong loser resolved"
        
        # =====================================================================
        # TEST 5: Gateway Natural Language Sentezleme (Synthesis)
        # =====================================================================
        print("\n--- Test 5: Gateway Natural Language Response Synthesis ---")
        ans_template = gw.generate_template_answer(q4, hits4, paths4, details4)
        print(f"Generated Template Answer:\n  {ans_template}")
        assert "primary finding is that Epoll is highly efficient" in ans_template, "Synthesis did not include primary node"
        assert "A contradiction between the claim" in ans_template, "Synthesis missing contradiction narrative"
        assert "resolved in favor of the latter based on confidence" in ans_template, "Synthesis missing resolution explanation"
        
        print("\n✓ Gateway natural language response synthesis verified.")
        print("\n🎉 All Provena v0.8 distributed integration tests passed successfully!")
        
    finally:
        print("\nTerminating domain servers...")
        proc_os.terminate()
        proc_chip.terminate()
        proc_os.wait()
        proc_chip.wait()
        cleanup()
        print("Done.")

if __name__ == "__main__":
    run_tests()
