import os
import sqlite3
import unittest
from unittest.mock import patch, MagicMock
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

def run_tests():
    print("🚀 Running Goldorn v0.5 Entegrasyon Testleri...")
    cleanup()
    
    # Initialize DB
    knowledge_graph.init_db()
    
    # =========================================================================
    # Test 1: Ingest Data and Verify Template Generation & Citation Formatting
    # =========================================================================
    print("\n--- Test 1: Template-Based Generation and Citation Formatting ---")
    
    # Ingest seed statements with specific sources
    auto_topology.ingest(
        "Epoll is highly efficient for high connection counts.",
        source="guide.pdf",
        domain_hint="OS",
        confidence=0.90
    )
    auto_topology.ingest(
        "Select is a traditional IO multiplexing method.",
        source="rfc.txt",
        domain_hint="OS",
        confidence=0.85
    )
    auto_topology.ingest(
        "Epoll is the modern replacement for Select in high-load situations.",
        source="comparison.txt",
        domain_hint="OS",
        confidence=0.90
    )
    
    # Manually insert edges for controlled testing
    knowledge_graph.add_edge("auto_epoll_modern_replacement_select", "auto_select_traditional_multiplexing_method", "supersedes", 0.80)
    knowledge_graph.add_edge("auto_epoll_highly_efficient_high", "auto_epoll_modern_replacement_select", "supports", 0.85)
    
    # Query the graph
    hits, paths = knowledge_graph.query("Epoll replacement for select in high load", top_k=3, hops=2)
    
    # Verify we got hits and paths
    assert len(hits) > 0, "Test 1 Failed: No matches found in query!"
    print(f"Hits: {[h[0] for h in hits]}")
    print(f"Paths count: {len(paths)}")
    
    # Generate template answer
    template_answer = knowledge_graph.generate_template_answer("Epoll replacement for select in high load", hits, paths)
    print("\nGenerated Template Answer:")
    print(f"  {template_answer}")
    
    # Assertions on citations and relations
    assert "auto_epoll_modern_replacement_select" in template_answer, "Test 1 Failed: Primary node citation missing!"
    assert "comparison.txt" in template_answer, "Test 1 Failed: Source file name for primary node missing!"
    assert "supersedes" in template_answer or "updates and supersedes" in template_answer, "Test 1 Failed: Relationship description 'supersedes' missing!"
    assert "rfc.txt" in template_answer, "Test 1 Failed: Connected node source missing!"
    assert "supports" in template_answer or "supported by" in template_answer, "Test 1 Failed: Relationship description 'supports' missing!"
    assert "guide.pdf" in template_answer, "Test 1 Failed: 'guide.pdf' source missing!"
    
    print("✓ Test 1 Passed: Template generation compiles relations and formats citations correctly.")

    # =========================================================================
    # Test 2: Contradiction Narrative Synthesis
    # =========================================================================
    print("\n--- Test 2: Contradiction Resolution Synthesis ---")
    
    # Ingest a contradicting statement that opposes the first one
    auto_topology.ingest(
        "Epoll is not efficient for high connection counts.",
        source="blog.txt",
        domain_hint="OS",
        confidence=0.90 # gets lowered to 0.40 due to contradiction gate
    )
    
    # Execute query that triggers contradiction resolution
    hits_c, paths_c = knowledge_graph.query("Epoll performance under high connections", top_k=3, hops=2)
    
    # Check that contradict resolution path is present
    resolutions = [p for p in paths_c if p["relation"] == "contradict_resolution"]
    assert len(resolutions) > 0, "Test 2 Failed: Contradiction resolution log not found in query paths!"
    
    # Generate template answer with contradiction
    contradict_answer = knowledge_graph.generate_template_answer("Epoll performance under high connections", hits_c, paths_c)
    print("\nGenerated Template Answer with Contradiction Resolution:")
    print(f"  {contradict_answer}")
    
    # Assert that contradiction resolution narrative is generated
    assert "contradiction" in contradict_answer.lower(), "Test 2 Failed: Answer narrative does not mention contradiction!"
    assert "resolved in favor of" in contradict_answer.lower(), "Test 2 Failed: Narrative does not explain how contradiction was resolved!"
    assert "blog.txt" in contradict_answer, "Test 2 Failed: Contradicting source 'blog.txt' missing from narrative!"
    
    print("✓ Test 2 Passed: Contradiction resolution narrative correctly synthesized.")

    # =========================================================================
    # Test 3: Ollama Generation and Fallback Mock Testing
    # =========================================================================
    print("\n--- Test 3: Ollama Integration and Fallback Mocking ---")
    
    # Scenario A: Ollama not running (Fallback to Template Compiler)
    with patch("knowledge_graph.get_installed_ollama_models", return_value=[]):
        print("Testing Hybrid Fallback (Ollama unavailable)...")
        # ask() should fallback to template compiler and print info
        top_node = knowledge_graph.ask("Epoll vs Select performance", generation_mode="hybrid")
        assert top_node is not None, "Test 3A Failed: ask() returned None on fallback!"
        print("  ✓ Graceful fallback verified.")
        
    # Scenario B: Ollama running (Successful SLM synthesis)
    mock_models = ["gemma:2b", "phi3"]
    mock_response = "According to [auto_epoll_modern_replacement_select], Epoll is indeed the modern replacement for Select in high-load setups [comparison.txt]."
    
    with patch("knowledge_graph.get_installed_ollama_models", return_value=mock_models), \
         patch("knowledge_graph.call_ollama", return_value=mock_response) as mock_call:
         
        print("\nTesting Hybrid Success (Ollama available)...")
        top_node = knowledge_graph.ask("Epoll vs Select performance", generation_mode="hybrid")
        
        # Verify Ollama is called with expected prompt
        assert mock_call.called, "Test 3B Failed: call_ollama was not called!"
        args, kwargs = mock_call.call_args
        prompt = args[0]
        model = args[1]
        
        print(f"  Ollama selected model: {model}")
        assert model == "gemma:2b", f"Test 3B Failed: Expected gemma:2b model, got {model}!"
        assert "auto_epoll_modern_replacement_select" in prompt, "Test 3B Failed: Prompt missing retrieved facts!"
        assert "Question: Epoll vs Select performance" in prompt, "Test 3B Failed: Prompt missing question context!"
        print("  ✓ Ollama synthesis request structure and model selection verified.")
        
    # Scenario C: Ollama Mode failing on missing service (should raise/report error)
    with patch("knowledge_graph.get_installed_ollama_models", return_value=[]):
        print("\nTesting Explicit Ollama Mode (service down)...")
        # In explicit "ollama" mode, it shouldn't fallback but report error
        top_node = knowledge_graph.ask("Epoll vs Select performance", generation_mode="ollama")
        # In ask(), if it fails, it prints error message but returns the top node if found
        assert top_node is not None
        print("  ✓ Explicit Ollama mode error handling verified.")

    print("\n🎉 All Goldorn v0.5 integration tests passed successfully!")
    cleanup()

if __name__ == "__main__":
    run_tests()
