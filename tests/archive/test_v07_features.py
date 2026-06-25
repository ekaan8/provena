import os
import sqlite3
import subprocess
import unittest

TEST_DB = "test_knowledge.db"
# Set environment variable so the child processes of the CLI will also use test_knowledge.db
os.environ["GOLDORN_DB_PATH"] = TEST_DB

def cleanup():
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except Exception as e:
            print(f"Error removing test DB: {e}")
            
    index_path = TEST_DB.replace(".db", ".index")
    if os.path.exists(index_path):
        try:
            os.remove(index_path)
        except Exception as e:
            print(f"Error removing test index: {e}")

def run_cli_command(args):
    # Execute the CLI tool in a subprocess with the env variable set
    cmd = ["./venv/bin/python3", "goldorn.py"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, env=os.environ)
    return result

def run_tests():
    print("🚀 Running Goldorn v0.7 CLI Integration Tests...")
    cleanup()
    
    # Initialize DB for CLI testing
    import knowledge_graph
    knowledge_graph.DB_PATH = TEST_DB
    knowledge_graph.init_db()
    
    # =========================================================================
    # Test 1: Add Node Command
    # =========================================================================
    print("\n--- Test 1: goldorn.py add ---")
    
    res1 = run_cli_command(["add", "Epoll is highly efficient for high connection counts.", "--domain", "OS", "--source", "guide.pdf", "--confidence", "0.90"])
    print(res1.stdout)
    assert res1.returncode == 0, f"Add node failed with stderr: {res1.stderr}"
    assert "Node added successfully" in res1.stdout, "Test 1 Failed: Success message missing from stdout!"
    assert "auto_epoll_highly_efficient_high" in res1.stdout, "Test 1 Failed: Generated ID missing from stdout!"
    
    # Add second node
    res2 = run_cli_command(["add", "Select is a traditional IO multiplexing method.", "--domain", "OS", "--source", "rfc.txt", "--confidence", "0.85"])
    assert res2.returncode == 0
    print("✓ Node addition verified via CLI.")

    # =========================================================================
    # Test 2: Ask Command
    # =========================================================================
    print("\n--- Test 2: goldorn.py ask ---")
    
    res3 = run_cli_command(["ask", "Epoll performance"])
    print(res3.stdout)
    assert res3.returncode == 0, f"Ask command failed with stderr: {res3.stderr}"
    assert "Natural Language Response" in res3.stdout, "Test 2 Failed: Output missing natural language generation header!"
    assert "Regarding the query" in res3.stdout, "Test 2 Failed: Template compiler did not generate answer text!"
    assert "Ollama Fallback" in res3.stdout, "Test 2 Failed: Mode tag missing!"
    print("✓ Ask query flow and Natural Language Response verified via CLI.")

    # =========================================================================
    # Test 3: Feedback Command
    # =========================================================================
    print("\n--- Test 3: goldorn.py feedback ---")
    
    # Run feedback reward
    # Manually add an edge first so that feedback has an edge to reward
    knowledge_graph.add_edge("auto_epoll_highly_efficient_high", "auto_select_traditional_multiplexing_method", "alternative_to", 0.5)
    
    res4 = run_cli_command(["feedback", "reward"])
    print(res4.stdout)
    assert res4.returncode == 0, f"Feedback command failed with stderr: {res4.stderr}"
    assert "Edge weights updated" in res4.stdout or "feedback applied" in res4.stdout or "management" in res4.stdout.lower(), "Test 3 Failed: Success message missing!"
    
    # Verify feedback registered in DB
    conn = sqlite3.connect(TEST_DB)
    fb = conn.execute("SELECT feedback FROM episodes ORDER BY id DESC LIMIT 1").fetchone()[0]
    conn.close()
    assert fb == 1, f"Test 3 Failed: Episode feedback was {fb}, expected 1!"
    print("✓ Path routing credit assignment feedback verified via CLI.")

    # =========================================================================
    # Test 4: Graph, History and Domains Summary Commands
    # =========================================================================
    print("\n--- Test 4: goldorn.py graph, history, domains ---")
    
    # Graph
    res_g = run_cli_command(["graph"])
    print(res_g.stdout)
    assert res_g.returncode == 0
    assert "Total Nodes:" in res_g.stdout and "2" in res_g.stdout, "Test 4 Failed: Node count incorrect in graph output!"
    assert "Total Edges:" in res_g.stdout and "1" in res_g.stdout, "Test 4 Failed: Edge count incorrect in graph output!"
    assert "Relation Distribution" in res_g.stdout, "Test 4 Failed: Missing relations section!"
    
    # History
    res_h = run_cli_command(["history"])
    print(res_h.stdout)
    assert res_h.returncode == 0
    assert "Episode Geçmişi" in res_h.stdout, "Test 4 Failed: History output header missing!"
    
    # Domains
    res_d = run_cli_command(["domains"])
    print(res_d.stdout)
    assert res_d.returncode == 0
    assert "OS" in res_d.stdout, "Test 4 Failed: Domains output missing 'OS' category!"
    
    print("✓ Graph, History, and Domains commands verified via CLI.")
    
    print("\n🎉 All Goldorn v0.7 CLI integration tests passed successfully!")
    cleanup()

if __name__ == "__main__":
    run_tests()
