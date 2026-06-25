#!/usr/bin/env python3
import sys
import os
import json
import sqlite3
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer

# Parse arguments first before importing core modules so that DB_PATH can be configured
parser = argparse.ArgumentParser(description="Provena Domain Knowledge Server")
parser.add_argument("--port", type=int, default=8000, help="Port to run the HTTP server on")
parser.add_argument("--db", type=str, required=True, help="Path to the SQLite database file")
args = parser.parse_args()

# Configure environment path for database override
os.environ["PROVENA_DB_PATH"] = args.db

import knowledge_graph
import auto_topology

# Update path dynamically to match command-line override
knowledge_graph.DB_PATH = args.db
knowledge_graph.init_db()

class DomainServerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Keep console output clean
        pass
        
    def _send_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/info":
            try:
                conn = sqlite3.connect(knowledge_graph.DB_PATH)
                total_nodes = conn.execute("SELECT count(*) FROM nodes").fetchone()[0]
                total_edges = conn.execute("SELECT count(*) FROM edges").fetchone()[0]
                
                # Retrieve dominant domain
                row = conn.execute(
                    "SELECT domain, count(*) FROM nodes WHERE domain IS NOT NULL GROUP BY domain ORDER BY count(*) DESC LIMIT 1"
                ).fetchone()
                domain_name = row[0] if row else "unknown"
                conn.close()
                
                info = {
                    "domain": domain_name,
                    "total_nodes": total_nodes,
                    "total_edges": total_edges,
                    "status": "online"
                }
                self._send_response(200, info)
            except Exception as e:
                self._send_response(500, {"error": str(e)})
        else:
            self._send_response(404, {"error": "Not Found"})
            
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        
        try:
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            self._send_response(400, {"error": "Invalid JSON"})
            return
            
        if self.path == "/query":
            question = payload.get("question")
            if not question:
                self._send_response(400, {"error": "Missing 'question' in payload"})
                return
                
            top_k = payload.get("top_k", 5)
            hops = payload.get("hops", 2)
            
            try:
                hits, paths = knowledge_graph.query(question, top_k=top_k, hops=hops)
                
                # Fetch details for all nodes involved in hits & paths
                node_ids = set([h[0] for h in hits])
                for p in paths:
                    node_ids.add(p["from"])
                    node_ids.add(p["to"])
                    
                node_details = {}
                if node_ids:
                    conn = sqlite3.connect(knowledge_graph.DB_PATH)
                    placeholders = ",".join(["?"] * len(node_ids))
                    rows = conn.execute(
                        f"SELECT id, content, confidence, source, domain, created_at FROM nodes WHERE id IN ({placeholders})",
                        list(node_ids)
                    ).fetchall()
                    conn.close()
                    for r in rows:
                        node_details[r[0]] = {
                            "id": r[0],
                            "content": r[1],
                            "confidence": r[2],
                            "source": r[3] if r[3] else "unknown",
                            "domain": r[4] if r[4] else "unknown",
                            "created_at": r[5]
                        }
                
                # Formulate response
                response_data = {
                    "hits": [
                        {
                            "id": h[0],
                            "content": h[1],
                            "confidence": h[2],
                            "score": h[3]
                        }
                        for h in hits
                    ],
                    "paths": paths,
                    "node_details": node_details
                }
                self._send_response(200, response_data)
            except Exception as e:
                self._send_response(500, {"error": str(e)})
                
        elif self.path == "/add":
            content = payload.get("content")
            domain = payload.get("domain")
            source = payload.get("source")
            confidence = payload.get("confidence", 0.8)
            node_id = payload.get("id")
            
            if not content or not domain or not source:
                self._send_response(400, {"error": "Missing required fields: 'content', 'domain', and 'source'"})
                return
                
            if not node_id:
                node_id = auto_topology.generate_node_id(content)
                
            try:
                # Check for duplicates first
                conn = sqlite3.connect(knowledge_graph.DB_PATH)
                existing = conn.execute("SELECT 1 FROM nodes WHERE id=?", (node_id,)).fetchone()
                conn.close()
                
                if existing:
                    import hashlib
                    suffix = hashlib.md5(content.encode()).hexdigest()[:6]
                    node_id = f"{node_id}_{suffix}"
                    
                knowledge_graph.add_node(node_id, content, source, confidence, domain)
                self._send_response(200, {
                    "success": True, 
                    "id": node_id, 
                    "message": "Node added successfully and index marked dirty."
                })
            except Exception as e:
                self._send_response(500, {"error": str(e)})
        else:
            self._send_response(404, {"error": "Not Found"})

def main():
    server_address = ("", args.port)
    class RobustHTTPServer(HTTPServer):
        allow_reuse_address = True
    httpd = RobustHTTPServer(server_address, DomainServerHandler)
    print(f"Starting Domain Server on port {args.port} using DB: {args.db}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Server stopped.")

if __name__ == "__main__":
    main()
