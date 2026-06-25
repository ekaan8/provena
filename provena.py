#!/usr/bin/env python3
import sys
import os
import argparse
import sqlite3
from datetime import date

# Import core modules
import knowledge_graph
import auto_topology

# ANSI terminal colors for premium CLI experience
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
RESET = "\033[0m"

def print_header(title):
    print(f"\n{BOLD}{CYAN}╔═{'═' * len(title)}═╗{RESET}")
    print(f"{BOLD}{CYAN}║ {title} ║{RESET}")
    print(f"{BOLD}{CYAN}╚═{'═' * len(title)}═╝{RESET}")

def handle_ask(args):
    print_header(f"ASK: {args.question}")
    knowledge_graph.ask(args.question, hops=args.hops, generation_mode=args.mode)

def handle_add(args):
    print_header("ADD NODE")
    node_id = auto_topology.generate_node_id(args.content)
    
    # Check if id already exists in SQLite
    conn = sqlite3.connect(knowledge_graph.DB_PATH)
    existing = conn.execute("SELECT 1 FROM nodes WHERE id=?", (node_id,)).fetchone()
    conn.close()
    
    if existing:
        import hashlib
        suffix = hashlib.md5(args.content.encode()).hexdigest()[:6]
        node_id = f"{node_id}_{suffix}"
        
    print(f"{BOLD}Content:{RESET} '{args.content}'")
    print(f"{BOLD}Domain:{RESET} {args.domain}")
    print(f"{BOLD}Source:{RESET} {args.source}")
    print(f"{BOLD}Confidence:{RESET} {args.confidence}")
    print(f"{BOLD}Generated ID:{RESET} {BLUE}{node_id}{RESET}")
    
    try:
        knowledge_graph.add_node(node_id, args.content, args.source, args.confidence, args.domain)
        print(f"\n{GREEN}✔ Node added successfully and FAISS index marked dirty!{RESET}")
    except Exception as e:
        print(f"\n{RED}❌ Error adding node: {e}{RESET}")

def handle_import(args):
    print_header("IMPORT DATA")
    
    # Try importing ingest_data
    try:
        import ingest_data
    except ImportError:
        print(f"{RED}❌ Could not import ingest_data helper.{RESET}")
        return
        
    path = args.path
    if not os.path.exists(path):
        print(f"{RED}❌ Specified path does not exist: {path}{RESET}")
        return
        
    print(f"{BOLD}Importing from:{RESET} {path}")
    print(f"{BOLD}Domain Hint:{RESET} {args.domain or 'Auto-detect'}")
    print(f"{BOLD}Starting Confidence:{RESET} {args.confidence}")
    
    try:
        if os.path.isfile(path):
            ingest_data.process_file(path, args.domain, args.confidence)
        elif os.path.isdir(path):
            files = [os.path.join(path, f) for f in os.listdir(path) 
                     if os.path.isfile(os.path.join(path, f))]
            valid_files = [f for f in files if os.path.splitext(f)[1].lower() in (".txt", ".pdf")]
            
            if not valid_files:
                print(f"{YELLOW}⚠️ No .txt or .pdf files found in directory: {path}{RESET}")
                return
                
            print(f"Found {len(valid_files)} valid files in directory.")
            for f in valid_files:
                ingest_data.process_file(f, args.domain, args.confidence)
        print(f"\n{GREEN}✔ Data import completed successfully!{RESET}")
    except Exception as e:
        print(f"\n{RED}❌ Error during import: {e}{RESET}")

def handle_feedback(args):
    print_header("FEEDBACK MANAGEMENT")
    
    conn = sqlite3.connect(knowledge_graph.DB_PATH)
    row = conn.execute("SELECT id, query, top_node, feedback FROM episodes ORDER BY id DESC LIMIT 1").fetchone()
    if not row:
        conn.close()
        print(f"{YELLOW}⚠️ No search history (episodes) found to apply feedback to.{RESET}")
        return
        
    episode_id, query_text, top_node, old_feedback = row
    print(f"{BOLD}Last Query:{RESET} '{query_text}'")
    print(f"{BOLD}Returned Node:{RESET} {BLUE}{top_node}{RESET}")
    print(f"{BOLD}Current Feedback Status:{RESET} {old_feedback}")
    
    print(f"\nApplying {BOLD}{args.type.upper()}{RESET} feedback...")
    hits, paths = knowledge_graph.query(query_text)
    
    fb_val = 1 if args.type == "reward" else -1
    result = knowledge_graph.blame_edge(paths, feedback=fb_val)
    
    if result:
        edge, new_w = result
        print(f"{GREEN}✔ Edge weights updated!{RESET}")
        # Update episode feedback in DB
        conn.execute("UPDATE episodes SET feedback = ? WHERE id = ?", (fb_val, episode_id))
        conn.commit()
    else:
        print(f"{YELLOW}⚠️ No active paths found or no update occurred (e.g. edge reached weight limits).{RESET}")
        
    conn.close()

def handle_graph(args):
    print_header("GRAPH SUMMARY AND METRICS")
    
    conn = sqlite3.connect(knowledge_graph.DB_PATH)
    total_nodes = conn.execute("SELECT count(*) FROM nodes").fetchone()[0]
    total_edges = conn.execute("SELECT count(*) FROM edges").fetchone()[0]
    
    relation_counts = conn.execute("SELECT relation, count(*) FROM edges GROUP BY relation ORDER BY count(*) DESC").fetchall()
    domain_counts = conn.execute("SELECT domain, count(*) FROM nodes GROUP BY domain ORDER BY count(*) DESC").fetchall()
    conn.close()
    
    print(f"{BOLD}Total Nodes:{RESET} {CYAN}{total_nodes}{RESET}")
    print(f"{BOLD}Total Edges:{RESET} {CYAN}{total_edges}{RESET}")
    
    print(f"\n{BOLD}{UNDERLINE}Relation Distribution:{RESET}")
    if relation_counts:
        for relation, count in relation_counts:
            print(f"  {YELLOW}{relation:<18}{RESET} : {count}")
    else:
        print("  No edges found.")
        
    print(f"\n{BOLD}{UNDERLINE}Domain Distribution:{RESET}")
    if domain_counts:
        for domain, count in domain_counts:
            print(f"  {GREEN}{domain or 'unknown':<18}{RESET} : {count}")
    else:
        print("  No nodes found.")

def handle_history(args):
    print_header(f"SEARCH HISTORY (Last {args.limit})")
    knowledge_graph.show_episodes(args.limit)

def handle_domains(args):
    print_header("DOMAINS LIST")
    conn = sqlite3.connect(knowledge_graph.DB_PATH)
    rows = conn.execute("SELECT domain, count(*) FROM nodes GROUP BY domain ORDER BY count(*) DESC").fetchall()
    conn.close()
    
    if not rows:
        print("No domains found.")
        return
        
    print(f"{BOLD}{'Domain':<20} | {'Node Count':<10}{RESET}")
    print("-" * 35)
    for domain, count in rows:
        dom_name = domain if domain else "unknown"
        print(f"{GREEN}{dom_name:<20}{RESET} | {count:<10}")

def main():
    parser = argparse.ArgumentParser(
        description="Provena CLI Tool - Manage Knowledge Graph and Query Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  {sys.argv[0]} ask "Epoll performance"
  {sys.argv[0]} add "GIL limits Python parallelism" --domain Programming --source "Python Docs"
  {sys.argv[0]} import data_folder/
  {sys.argv[0]} feedback reward
  {sys.argv[0]} graph
  {sys.argv[0]} history
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommands")
    
    # Subcommand: ask
    parser_ask = subparsers.add_parser("ask", help="Query the knowledge engine")
    parser_ask.add_argument("question", help="The question to ask")
    parser_ask.add_argument("--hops", type=int, default=2, help="Graph search hops (default: 2)")
    parser_ask.add_argument("--mode", default="hybrid", choices=["hybrid", "template", "ollama"], 
                            help="Language Generation Mode (default: hybrid)")
    
    # Subcommand: add
    parser_add = subparsers.add_parser("add", help="Add a single node to the database")
    parser_add.add_argument("content", help="Node statement content")
    parser_add.add_argument("--domain", required=True, help="Domain category of the knowledge claim")
    parser_add.add_argument("--source", required=True, help="Source of the claim (e.g. document name, url)")
    parser_add.add_argument("--confidence", type=float, default=0.8, help="Confidence value between 0.0 and 1.0")
    
    # Subcommand: import
    parser_import = subparsers.add_parser("import", help="Import PDF/TXT files or directories")
    parser_import.add_argument("path", help="Path to PDF/TXT file or directory containing them")
    parser_import.add_argument("--domain", default=None, help="Domain hint category")
    parser_import.add_argument("--confidence", type=float, default=0.75, help="Starting confidence")
    
    # Subcommand: feedback
    parser_feedback = subparsers.add_parser("feedback", help="Reward or blame the last query's active path")
    parser_feedback.add_argument("type", choices=["reward", "blame"], help="Type of feedback to apply")
    
    # Subcommand: graph
    subparsers.add_parser("graph", help="Show summary statistics of the graph")
    
    # Subcommand: history
    parser_history = subparsers.add_parser("history", help="Show query episode history")
    parser_history.add_argument("--limit", type=int, default=10, help="Number of records to show")
    
    # Subcommand: domains
    subparsers.add_parser("domains", help="List domains and node distribution")
    
    args = parser.parse_args()
    
    # Execute commands
    if args.command == "ask":
        handle_ask(args)
    elif args.command == "add":
        handle_add(args)
    elif args.command == "import":
        handle_import(args)
    elif args.command == "feedback":
        handle_feedback(args)
    elif args.command == "graph":
        handle_graph(args)
    elif args.command == "history":
        handle_history(args)
    elif args.command == "domains":
        handle_domains(args)

if __name__ == "__main__":
    main()
