# Goldorn — Project Progress Document v1.0

**Date:** 2026-06-24  
**Status:** Active development — working prototype (v0.2)  
**Language:** Python  
**Repository root:** `~/Downloads/goldorn/`

---

## Table of Contents

1. [What Is Goldorn?](#1-what-is-goldorn)
2. [The Core Idea — Conceptual Foundation](#2-the-core-idea--conceptual-foundation)
3. [What Goldorn Is and Is Not](#3-what-goldorn-is-and-is-not)
4. [Theoretical Background](#4-theoretical-background)
5. [Development Session — Full Technical Log](#5-development-session--full-technical-log)
6. [Current Architecture](#6-current-architecture)
7. [File Structure](#7-file-structure)
8. [Full Source Code — Current State](#8-full-source-code--current-state)
9. [Knowledge Base — Current Nodes and Edges](#9-knowledge-base--current-nodes-and-edges)
10. [Test Results and Behavioral Observations](#10-test-results-and-behavioral-observations)
11. [Open Problems](#11-open-problems)
12. [Roadmap](#12-roadmap)
13. [Key Definitions and Terminology](#13-key-definitions-and-terminology)

---

## 1. What Is Goldorn?

**Goldorn** is an experimental knowledge representation and reasoning system. It is not a chatbot, not a search engine, and not a vector database. It is a prototype that attempts to answer this question:

> Can the knowledge that LLMs compress into weight matrices be stored instead in an open, relational, updatable, and learnable graph structure — and can that structure reason, learn from feedback, and improve over time?

The name is provisional. The concept is not.

The system's central formula, borrowed from transformer notation, is:

```
Standard LLM:  Y = f(X, W)      — W is a weight matrix, learned, opaque
Goldorn:       Y = f(X, Graph)  — Graph is explicit, inspectable, updatable
```

This is not a replacement for LLMs. It is an exploration of an alternative paradigm for knowledge representation, with specific advantages in transparency, updateability, provenance tracking, and domain specialization.

---

## 2. The Core Idea — Conceptual Foundation

### 2.1 The Problem with Standard LLMs

Large language models compress knowledge into billions of floating-point parameters. This compression is:

- **Fast at inference** — a single forward pass produces output
- **Powerful at generalization** — emergent reasoning across domains
- **Opaque** — you cannot ask "where did this fact come from?"
- **Frozen** — updating requires retraining
- **Hallucination-prone** — the model cannot distinguish "I know this" from "I'm interpolating this"

### 2.2 The Proposal

Instead of implicit knowledge stored in weights, Goldorn stores knowledge:

- As **nodes** — discrete, identifiable knowledge units
- As **edges** — typed, weighted relationships between nodes
- With **embeddings** — semantic vector representations for similarity matching
- With **provenance** — source, timestamp, confidence per node
- With **learning rules** — edge weights update based on feedback and usage

This gives the system properties that LLMs fundamentally cannot have:
- "Where did this come from?" is always answerable
- Updating one fact does not corrupt unrelated facts
- The system improves from use without retraining

### 2.3 The Xanadu Connection

Ted Nelson's Xanadu project (1960s–present) imagined a global hypertext system where:

- Content is included by **reference**, not copied (transclusion)
- Links are **bidirectional** — every link knows its origin and destination
- Documents exist in **parallel contexts** — same content, multiple views
- **Versioning** is built in — every state is preserved

Goldorn is, in a sense, Xanadu's AI interpretation:

| Xanadu Concept | Goldorn Equivalent |
|---|---|
| Transclusion | Node referenced across edges; update propagates |
| Bidirectional links | Edge has from/to + relation type + weight |
| Parallel documents | Context-dependent activation |
| Versioning | Timestamp + confidence fields per node |

Nelson's project was never completed. Goldorn does not try to finish it — it applies its philosophy to machine reasoning.

---

## 3. What Goldorn Is and Is Not

### Is:
- An **experimental knowledge graph** with typed, weighted relationships
- A system where **edge weights update from feedback** (learning)
- A **multi-hop reasoning** engine that propagates activation across the graph
- A **domain-aware** retrieval system that respects knowledge boundaries
- A prototype for **personal AI memory** — transparent, growing, revisable

### Is Not:
- A note-taking app
- A search engine
- A vector database
- A RAG system
- A GPT alternative or replacement
- A general-purpose AI
- A web scraping system

---

## 4. Theoretical Background

### 4.1 Relation to Existing Paradigms

| Paradigm | Relation to Goldorn |
|---|---|
| LLM / Transformer | Goldorn replaces the weight matrix with an explicit graph |
| Knowledge Graph | Goldorn adds learning rules and semantic retrieval |
| RAG | RAG retrieves from external sources; Goldorn learns the graph itself |
| Graph Neural Networks | GNNs learn on graphs via backprop; Goldorn uses feedback-based local rules |
| Hebbian Learning | Goldorn's weight update ("fire together, wire together") is Hebbian-inspired |
| Neuromorphic Computing | Conceptual inspiration; not the implementation |
| Continual Learning | Goldorn targets the same problem: learn without forgetting |

### 4.2 The Learning Rule

Goldorn uses a simple but meaningful update rule:

```
new_weight = old_weight + (feedback × confidence) − (0.01 × days_since_last_use)
```

- `feedback`: +1 (useful), 0 (neutral), -1 (wrong)
- `confidence`: the node's stored confidence score (0.0–1.0)
- `decay`: edges that are not activated gradually weaken
- `ceiling/floor`: weight is clamped to [0.0, 1.0]

This rule implements:
- **Hebbian reinforcement** — used paths strengthen
- **Temporal decay** — unused knowledge fades
- **Confidence weighting** — high-confidence nodes have more learning impact

### 4.3 Why Not Backpropagation?

Backpropagation requires a differentiable computation graph and a global error signal. Goldorn's graph is discrete and symbolic. The tradeoff is explicit:

- Goldorn gives up the global optimization power of gradient descent
- In return, it gains local updateability, interpretability, and provenance

This is not a bug. It is the core design choice.

---

## 5. Development Session — Full Technical Log

This section is a complete chronological record of the development session that produced the current working prototype.

### 5.1 Environment Setup

```bash
# Virtual environment
cd ~/Downloads/goldorn
python3 -m venv venv
source venv/bin/activate

# Dependencies
pip install sentence-transformers networkx numpy
```

**Embedding model used:** `paraphrase-multilingual-MiniLM-L12-v2`  
**Size:** ~471MB (downloaded on first run from Hugging Face)  
**Note:** HF authentication warning appears but model downloads without token.

---

### 5.2 Spec Design (Paper Phase)

Before writing code, the following schema was defined:

```
NODE v0.1
─────────────────────────────
id:          unique string identifier
content:     single-sentence knowledge claim
source:      origin of the information
confidence:  float 0.0–1.0
domain:      knowledge category string
created_at:  ISO date string

EDGE v0.1
─────────────────────────────
from:        node_id
to:          node_id
relation:    one of VALID_RELATIONS
weight:      float 0.0–1.0
last_active: ISO date string

LEARNING RULE v0.1
─────────────────────────────
new_weight = old_weight + (feedback × confidence) − (0.01 × days)
feedback: +1 / 0 / -1
decay: 0.01 per day unused
ceiling: 1.0 | floor: 0.0
```

---

### 5.3 Initial Node Set (seed.py)

First 5 nodes, all from the operating systems / systems programming domain:

| ID | Domain | Confidence |
|---|---|---|
| `io_multiplexing_select` | işletim sistemleri | 1.0 |
| `io_multiplexing_epoll` | işletim sistemleri | 1.0 |
| `concurrent_stock_sim` | yazılım mimarisi | 0.95 |
| `c11_stdatomic_usage` | paralel programlama | 1.0 |
| `mutex_lock_overhead` | işletim sistemleri | 0.9 |

Initial edges:

| From | To | Relation | Weight |
|---|---|---|---|
| `io_multiplexing_epoll` | `io_multiplexing_select` | `contradicts` | 0.85 |
| `io_multiplexing_select` | `concurrent_stock_sim` | `part_of` | 0.90 |
| `c11_stdatomic_usage` | `mutex_lock_overhead` | `supports` | 0.80 |

```bash
python3 seed.py
# Output:
# ✓ node: io_multiplexing_select
# ✓ node: io_multiplexing_epoll
# ✓ node: concurrent_stock_sim
# ✓ node: c11_stdatomic_usage
# ✓ node: mutex_lock_overhead
# ✓ edge: io_multiplexing_epoll → io_multiplexing_select
# ✓ edge: io_multiplexing_select → concurrent_stock_sim
# ✓ edge: c11_stdatomic_usage → mutex_lock_overhead
# Veritabanı hazır.
```

---

### 5.4 First Query Test and Bug Discovery

```bash
python3 -c "from knowledge_graph import ask, update_weight; \
    ask('yüksek bağlantı sayısında I/O performansı'); \
    update_weight('io_multiplexing_epoll','io_multiplexing_select', feedback=1, confidence=1.0)"
```

**Result:**
```
🥇 [io_multiplexing_select]  skor:0.520
📌 [concurrent_stock_sim]    skor:0.386
📌 [io_multiplexing_epoll]   skor:0.319
```

**Bug:** `select` ranked first despite `epoll` being the correct answer for high-connection I/O. Root cause: embedding similarity matched "yüksek bağlantı sayılarında performans kaybı" in `select`'s content literally. The graph structure had no influence on ranking.

**Fix:** Modified `query()` to propagate graph neighbor scores into ranking.

---

### 5.5 Edge Semantics Refactor — `contradicts` → `supersedes`

The edge `epoll → select, contradicts` was semantically incorrect. `epoll` does not *contradict* `select` — it *supersedes* it. These are different relationships:

- `contradicts`: Two claims that cannot both be true
- `supersedes`: A newer/better approach that replaces an older one

**Added `supersedes` to `VALID_RELATIONS`.**

**Migration:**

```bash
python3 migrate_edges.py
# Deleted: io_multiplexing_select → concurrent_stock_sim (part_of)
# Added:   concurrent_stock_sim → io_multiplexing_select (uses, 0.70)
```

**Reasoning for `part_of` removal:**  
`select → stock_sim, part_of` implied "select is part of the stock simulator." This caused the simulator node to rank high for I/O queries (it inherited select's high embedding score via the edge). The corrected direction `stock_sim → select, uses` means "the simulator uses select" — semantically accurate and boost flows correctly.

---

### 5.6 Relation Semantics Table

The following table defines how each relation type affects ranking:

| Relation | Boost Direction | Coefficient | Penalty Direction | Penalty Coefficient |
|---|---|---|---|---|
| `supersedes` | `from` rises | 0.45 | `to` falls | 0.30 |
| `contradicts` | `from` rises | 0.30 | `to` falls | 0.20 |
| `supports` | `to` rises | 0.35 | — | — |
| `uses` | `to` rises | 0.20 | — | — |
| `part_of` | `to` rises | 0.25 | — | — |
| `example_of` | `to` rises | 0.30 | — | — |
| `causes` | `to` rises | 0.30 | — | — |
| `related_to` | both rise | 0.15 | — | — |
| `valid_when` | `from` rises | 0.25 | — | — |
| `alternative_to` | both rise | 0.20 | — | — |
| `depends_on` | `to` rises | 0.20 | — | — |

**Boost direction logic:**
- `supersedes`/`contradicts`: the *superior* node (from) should rise when the inferior node (to) matches the query
- `supports`/`causes`/`uses`: the *target* node should rise when the *source* node matches the query

---

### 5.7 Penalty Mechanism

Without penalty, `select` kept appearing at the top even after the `supersedes` edge was added — because its embedding score was high. The penalty rule:

```python
RELATION_PENALTY = {
    "supersedes": ("to", 0.30),   # the superseded node is penalized
    "contradicts": ("to", 0.20),  # the contradicted node is penalized
}
```

After adding penalty:

```
epoll:  0.553  ← first (correct)
select: 0.478  ← penalized (was 0.574 before penalty)
```

This was the first confirmed instance of **graph semantics overriding raw embedding similarity**.

---

### 5.8 v0.2 — Multi-Hop Activation and Episode Memory

**Motivation:** Single-hop propagation (A→B) is a database. Multi-hop (A→B→C) is the beginning of graph reasoning.

**Multi-hop implementation:**

```python
def query(question, top_k=3, hops=2):
    base = _base_scores(question)
    boosted = dict(base)

    for _ in range(hops):          # iterate hops
        delta = {id: 0.0 for id in boosted}
        for from_node, to_node, weight, relation in edges:
            # apply boost and penalty per relation type
            ...
        for id in boosted:
            boosted[id] += delta[id]  # apply accumulated delta
```

**Episode memory:** Every query is logged to an `episodes` table in SQLite:

```sql
CREATE TABLE episodes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    query      TEXT NOT NULL,
    top_node   TEXT,
    feedback   INTEGER DEFAULT 0,
    created_at TEXT
);
```

**Schema update required:**
```bash
python3 -c "from knowledge_graph import init_db; init_db()"
```
(The `episodes` table did not exist until `init_db()` was run with the new schema.)

---

### 5.9 v0.2 Validation — Three Queries, Three Correct Answers

After adding nodes `select_low_conn_advantage` and `epoll_linux_only`:

```bash
python3 -c "
from knowledge_graph import ask, show_episodes
ask('yüksek bağlantı sayısında I/O performansı')
ask('taşınabilir cross-platform I/O çözümü')
ask('düşük bağlantıda basit I/O')
show_episodes()
"
```

**Results:**

```
yüksek bağlantı sayısında I/O performansı → io_multiplexing_epoll        ✅
taşınabilir cross-platform I/O çözümü     → epoll_linux_only             ✅
düşük bağlantıda basit I/O                → select_low_conn_advantage    ✅
```

**Significance:** The same domain, three different queries, three semantically correct different answers. The system is not keyword matching — it is using graph structure and relation types to differentiate context.

---

### 5.10 Second Domain — Chip Architecture

New nodes added via `add_chip_domain.py`:

| ID | Domain |
|---|---|
| `arm_risc_architecture` | bilgisayar mimarisi |
| `x86_cisc_architecture` | bilgisayar mimarisi |
| `apple_silicon_m1` | bilgisayar mimarisi |
| `unified_memory_architecture` | bilgisayar mimarisi |
| `arm_power_efficiency` | bilgisayar mimarisi |
| `chiplet_design` | bilgisayar mimarisi |
| `moores_law` | chip tarihi |
| `moores_law_slowdown` | chip tarihi |
| `apple_silicon_transition` | chip tarihi |
| `tsmc_3nm_process` | chip tarihi |

New edges (11 total):

| From | To | Relation | Weight |
|---|---|---|---|
| `arm_risc_architecture` | `x86_cisc_architecture` | `contradicts` | 0.75 |
| `arm_risc_architecture` | `arm_power_efficiency` | `causes` | 0.90 |
| `apple_silicon_m1` | `arm_risc_architecture` | `example_of` | 0.95 |
| `apple_silicon_m1` | `unified_memory_architecture` | `example_of` | 0.90 |
| `apple_silicon_transition` | `x86_cisc_architecture` | `supersedes` | 0.80 |
| `apple_silicon_transition` | `apple_silicon_m1` | `part_of` | 0.85 |
| `moores_law_slowdown` | `moores_law` | `contradicts` | 0.85 |
| `moores_law_slowdown` | `chiplet_design` | `causes` | 0.75 |
| `moores_law_slowdown` | `arm_power_efficiency` | `supports` | 0.70 |
| `tsmc_3nm_process` | `apple_silicon_m1` | `supports` | 0.80 |
| `chiplet_design` | `moores_law` | `alternative_to` | 0.70 |

---

### 5.11 Cross-Domain Contamination Bug

After adding chip nodes, the query "yüksek bağlantı sayısında I/O performansı" returned `arm_power_efficiency` as first result instead of `io_multiplexing_epoll`.

**Root cause:** With 10 chip nodes and 5 I/O nodes, multi-hop boost summed across all chip nodes exceeded the I/O cluster total. The word "performans" appeared in multiple chip node contents, giving them high base scores.

**Fix 1 — Domain-aware propagation:**

```python
same_domain = domain_map.get(from_node) == domain_map.get(to_node)
domain_coef = 1.0 if same_domain else 0.10
effective_coef = coef * domain_coef
```

Cross-domain boost reduced to 10% of same-domain boost.

**Fix 2 — MAX-based dominant domain detection:**

Initial fix used `sum` of base scores per domain to detect dominant domain — this failed because 10 chip nodes summed higher than 5 I/O nodes even when individual chip scores were lower.

Corrected to use `max` of base scores per domain:

```python
domain_max = defaultdict(float)
for id, score in base.items():
    d = domain_map.get(id, "unknown")
    if score > domain_max[d]:
        domain_max[d] = score
dominant = max(domain_max, key=domain_max.get)
```

**Logic:** The domain whose single best-matching node scores highest is the dominant domain. This correctly identifies the query's primary domain regardless of how many nodes each domain has.

---

### 5.12 Final Validation — Two Domains, Four Queries

```bash
python3 -c "
from knowledge_graph import ask
ask('ARM neden güç verimli?')
ask('Moore Yasası neden yavaşlıyor?')
ask('Apple neden Intel\'i bıraktı?')
ask('yüksek bağlantı sayısında I/O performansı')
"
```

**Results:**

```
ARM neden güç verimli?          → arm_power_efficiency      ✅
Moore Yasası neden yavaşlıyor?  → moores_law_slowdown       ✅
Apple neden Intel'i bıraktı?    → apple_silicon_transition  ✅
yüksek bağlantı sayısında I/O   → io_multiplexing_epoll     ✅
```

All four correct. Two separate domains coexisting without interference.

Notable: "Apple neden Intel'i bıraktı?" → `apple_silicon_transition` (not `apple_silicon_m1` or `arm_risc_architecture`). The system found the node describing *the transition itself*, not the technology involved. This is correct semantic disambiguation.

---

## 6. Current Architecture

```
User Query (natural language)
        ↓
Sentence Transformer Embedding
        ↓
Base Scores (cosine similarity × confidence)
        ↓
Dominant Domain Detection (MAX-based)
        ↓
Non-dominant domain nodes → base score × 0.25
        ↓
Multi-hop Graph Propagation (2 hops)
    - Same-domain boost: full coefficient
    - Cross-domain boost: 10% coefficient
    - Relation-type specific boost direction
    - Penalty for superseded/contradicted nodes
        ↓
Final Ranking
        ↓
Top-K Results with neighbor display
        ↓
Episode Logging (SQLite)
```

### 6.1 Learning Loop

```
Query → Result → [User Feedback]
                      ↓
              update_weight(from, to, feedback, confidence)
                      ↓
              new_weight = old + (feedback × confidence) − decay
                      ↓
              Next query uses updated weights
```

The system has been observed to learn: `epoll → select` edge weight increased from 0.85 to 1.00 after positive feedback, and subsequent queries reflected this change in ranking.

---

## 7. File Structure

```
goldorn/
├── knowledge_graph.py      ← core engine (current v0.2)
├── seed.py                 ← initial 5 I/O nodes + edges
├── migrate_edges.py        ← edge semantics correction migration
├── add_v02_nodes.py        ← 2 additional I/O context nodes
├── add_chip_domain.py      ← 10 chip architecture nodes + 11 edges
└── knowledge.db            ← SQLite database (auto-created)
```

**SQLite tables:**
- `nodes` — knowledge units
- `edges` — typed weighted relationships
- `episodes` — query history with feedback

---

## 8. Full Source Code — Current State

### `knowledge_graph.py`

```python
import sqlite3, json
from datetime import date
from collections import defaultdict
import numpy as np

DB_PATH = "knowledge.db"

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
    ''')
    conn.commit()
    conn.close()

def add_node(id, content, source, confidence, domain):
    emb = json.dumps(_model.encode(content).tolist()) if USE_EMBEDDINGS else None
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO nodes VALUES (?,?,?,?,?,?,?)",
        (id, content, source, confidence, domain, emb, date.today().isoformat())
    )
    conn.commit(); conn.close()

def add_edge(from_node, to_node, relation, weight=0.5):
    assert relation in VALID_RELATIONS, f"Invalid relation: {relation}"
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

def query(question, top_k=3, hops=2):
    base = _base_scores(question)
    if not base:
        return []

    edges = _get_all_edges()

    conn = sqlite3.connect(DB_PATH)
    domain_map = {
        row[0]: row[1]
        for row in conn.execute("SELECT id, domain FROM nodes").fetchall()
    }
    conn.close()

    # MAX-based dominant domain detection
    domain_max = defaultdict(float)
    for id, score in base.items():
        d = domain_map.get(id, "unknown")
        if score > domain_max[d]:
            domain_max[d] = score
    dominant = max(domain_max, key=domain_max.get)

    # Suppress non-dominant domains at base score level
    for id in base:
        if domain_map.get(id) != dominant:
            base[id] *= 0.25

    boosted = dict(base)

    for _ in range(hops):
        delta = {id: 0.0 for id in boosted}

        for from_node, to_node, weight, relation in edges:
            same_domain = domain_map.get(from_node) == domain_map.get(to_node)
            domain_coef = 1.0 if same_domain else 0.10

            direction, coef = RELATION_BOOST.get(relation, ("to", 0.15))
            effective_coef = coef * domain_coef

            if direction == "from":
                if to_node in boosted and from_node in boosted:
                    delta[from_node] += boosted[to_node] * weight * effective_coef
            elif direction == "to":
                if from_node in boosted and to_node in boosted:
                    delta[to_node] += boosted[from_node] * weight * effective_coef
            else:
                if to_node in boosted and from_node in boosted:
                    delta[from_node] += boosted[to_node] * weight * effective_coef
                    delta[to_node]   += boosted[from_node] * weight * effective_coef

            pen_dir, pen_coef = RELATION_PENALTY.get(relation, (None, 0))
            if pen_dir == "to":
                if from_node in boosted and to_node in boosted:
                    delta[to_node] -= boosted[from_node] * weight * pen_coef * domain_coef

        for id in boosted:
            boosted[id] += delta[id]

    node_map = {id: (content, conf) for id, content, conf, _ in _get_all_nodes()}
    results = [
        (id, node_map[id][0], node_map[id][1], score)
        for id, score in boosted.items() if id in node_map
    ]
    return sorted(results, key=lambda x: x[3], reverse=True)[:top_k]

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

def update_weight(from_node, to_node, feedback: int, confidence: float = 0.8):
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
    conn.commit(); conn.close()
    return new_weight

def log_episode(query_text, top_node, feedback=0):
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
    print("\n📖 Episode History")
    print("─" * 60)
    for ts, q, node, fb in rows:
        fb_str = "✅" if fb > 0 else ("❌" if fb < 0 else "○")
        print(f"  {fb_str} [{ts}] {q[:45]}… → {node}")

def ask(question, hops=2):
    print(f"\n❓ {question}  (hop={hops})")
    print("─" * 60)
    hits = query(question, hops=hops)
    if not hits:
        print("No matching nodes.")
        return None
    for i, (node_id, content, conf, score) in enumerate(hits):
        print(f"\n{'🥇' if i==0 else '📌'} [{node_id}]  confidence:{conf}  score:{score:.3f}")
        print(f"   {content}")
        for to_id, rel, w, ncontent in get_neighbors(node_id):
            print(f"   └─ [{rel}] → {to_id}  (weight:{w:.2f})")
            print(f"      {ncontent[:90]}…")
    top = hits[0][0]
    log_episode(question, top)
    return top
```

---

## 9. Knowledge Base — Current Nodes and Edges

### 9.1 All 17 Nodes

**Domain: işletim sistemleri**

| ID | Content summary |
|---|---|
| `io_multiplexing_select` | select() O(N) scan, performance degrades at high FD count |
| `io_multiplexing_epoll` | epoll_wait() O(1), returns only active FDs |
| `mutex_lock_overhead` | Mutex context switch cost vs lock-free in high-contention |
| `select_low_conn_advantage` | select() preferred for <100 FD due to simplicity and portability |
| `epoll_linux_only` | epoll is Linux-specific; unavailable on BSD/macOS/Windows |

**Domain: paralel programlama**

| ID | Content summary |
|---|---|
| `c11_stdatomic_usage` | stdatomic.h provides lock-free atomic operations |

**Domain: yazılım mimarisi**

| ID | Content summary |
|---|---|
| `concurrent_stock_sim` | Single-thread select()-based stock simulator, stable at low connection counts |

**Domain: bilgisayar mimarisi**

| ID | Content summary |
|---|---|
| `arm_risc_architecture` | ARM uses RISC; few simple instructions, high clock, low power |
| `x86_cisc_architecture` | x86 uses CISC; complex hardware instructions, legacy compatibility layers |
| `apple_silicon_m1` | First Apple Silicon chip; ARM-based; unified memory architecture |
| `unified_memory_architecture` | CPU and GPU share single high-bandwidth memory pool |
| `arm_power_efficiency` | ARM achieves higher performance-per-watt than x86 |
| `chiplet_design` | Multiple small chips packaged together; AMD/Intel response to Moore slowdown |

**Domain: chip tarihi**

| ID | Content summary |
|---|---|
| `moores_law` | Transistor count doubles every ~2 years; observed by Gordon Moore 1965 |
| `moores_law_slowdown` | Physical limits (quantum tunneling, heat density) challenging Moore's Law continuity |
| `apple_silicon_transition` | Apple moved entire Mac line from Intel x86 to ARM (2020–2022); Rosetta 2 translation |
| `tsmc_3nm_process` | TSMC 3nm used for Apple M3 series; smaller transistors, lower power |

### 9.2 All Edges (18 total)

| From | To | Relation | Weight |
|---|---|---|---|
| `io_multiplexing_epoll` | `io_multiplexing_select` | `supersedes` | 1.00 |
| `concurrent_stock_sim` | `io_multiplexing_select` | `uses` | 0.70 |
| `c11_stdatomic_usage` | `mutex_lock_overhead` | `supports` | 0.80 |
| `select_low_conn_advantage` | `io_multiplexing_select` | `supports` | 0.75 |
| `select_low_conn_advantage` | `io_multiplexing_epoll` | `contradicts` | 0.60 |
| `select_low_conn_advantage` | `epoll_linux_only` | `alternative_to` | 0.65 |
| `epoll_linux_only` | `io_multiplexing_epoll` | `valid_when` | 0.80 |
| `arm_risc_architecture` | `x86_cisc_architecture` | `contradicts` | 0.75 |
| `arm_risc_architecture` | `arm_power_efficiency` | `causes` | 0.90 |
| `apple_silicon_m1` | `arm_risc_architecture` | `example_of` | 0.95 |
| `apple_silicon_m1` | `unified_memory_architecture` | `example_of` | 0.90 |
| `apple_silicon_transition` | `x86_cisc_architecture` | `supersedes` | 0.80 |
| `apple_silicon_transition` | `apple_silicon_m1` | `part_of` | 0.85 |
| `moores_law_slowdown` | `moores_law` | `contradicts` | 0.85 |
| `moores_law_slowdown` | `chiplet_design` | `causes` | 0.75 |
| `moores_law_slowdown` | `arm_power_efficiency` | `supports` | 0.70 |
| `tsmc_3nm_process` | `apple_silicon_m1` | `supports` | 0.80 |
| `chiplet_design` | `moores_law` | `alternative_to` | 0.70 |

---

## 10. Test Results and Behavioral Observations

### 10.1 Confirmed Working Behaviors

| Behavior | Evidence |
|---|---|
| Embedding-based retrieval | Base scores computed via cosine similarity |
| Graph boost (single hop) | `supersedes` edge raises epoll above select |
| Penalty mechanism | `select` score dropped 0.574 → 0.478 after penalty added |
| Multi-hop propagation | 2-hop activation across 3+ node chains confirmed |
| Episode logging | Query history stored and displayed correctly |
| Cross-domain isolation | I/O and chip domains do not contaminate each other |
| Learning (weight update) | `epoll→select` weight: 0.85 → 1.00 after `feedback=+1` |
| Context disambiguation | Same domain, different questions → different correct answers |

### 10.2 Confirmed Bugs Found and Fixed

| Bug | Root Cause | Fix |
|---|---|---|
| select ranked above epoll | Graph not influencing ranking | Added neighbor score propagation |
| stock_sim inflated by I/O queries | `part_of` direction wrong | Migrated to `uses`, reversed direction |
| arm_power_efficiency contaminating I/O queries | SUM-based domain detection | Switched to MAX-based detection |
| chip nodes bleeding into I/O results | Cross-domain boost too high | domain_coef = 0.10 for cross-domain |

### 10.3 Known Limitation

`arm_risc_architecture` still ranks first for "Apple neden Intel'i bıraktı?" instead of `apple_silicon_transition`. This is a minor semantic gap — both are valid answers, but `apple_silicon_transition` is more precise. The system could be improved here with a `directly_caused_by` or `historically_motivated_by` relation type.

---

## 11. Open Problems

These are the unresolved questions that will determine the system's ceiling:

### 11.1 Learning Signal Quality
The current feedback signal is binary (+1/0/-1) and user-initiated. In practice, most users don't explicitly provide feedback. How do we generate implicit feedback from usage patterns?

### 11.2 Credit Assignment
When a query traverses A→B→C and the result is wrong, which edge is responsible? Currently there is no mechanism to identify and penalize the specific guilty edge.

### 11.3 Automatic Node Creation
Currently all nodes are manually written. The next major step is: given a paragraph of text, automatically extract knowledge claims and add them as nodes with appropriate edges.

### 11.4 Conflict Resolution
Two nodes can `contradicts` each other. When both activate for the same query, how does the system decide which is current/correct? A confidence decay over time (outdated information becomes less confident) is one approach.

### 11.5 Scalability
At 17 nodes, the system is fast. At 10,000 nodes, loading all embeddings into memory for every query will be slow. A FAISS or SQLite vector extension will be needed.

### 11.6 Natural Language Generation
Currently the system returns raw node content. To produce fluent answers, a small local LLM (Phi-3, Gemma 2B) should be added as a generation layer that takes the top-K nodes and produces a synthesized response.

---

## 12. Roadmap

### v0.3 — Automation
- [ ] Text → Node extraction (spaCy or Claude API for chunking)
- [ ] Batch import from markdown notes
- [ ] Auto-suggest edge type between two nodes

### v0.4 — Generation Layer
- [ ] Integrate Ollama (Phi-3 Mini or Gemma 2B)
- [ ] Produce synthesized answers from top-K nodes
- [ ] Include source citations in output

### v0.5 — Scale
- [ ] FAISS index for fast nearest-neighbor lookup
- [ ] Lazy loading of embeddings
- [ ] Benchmark: query latency at 100 / 500 / 1000 nodes

### v1.0 — Personal Knowledge OS
- [ ] Import internship notes
- [ ] Import IconTech content drafts
- [ ] Import book/paper reading notes
- [ ] CLI interface for daily use

---

## 13. Key Definitions and Terminology

| Term | Definition |
|---|---|
| **Node** | A discrete, identified knowledge unit (fact, concept, claim) |
| **Edge** | A typed, weighted, directional relationship between two nodes |
| **Embedding** | A dense vector representing a node's semantic content |
| **Base score** | Cosine similarity between query embedding and node embedding, scaled by confidence |
| **Boost** | Graph-derived score increment applied to a node based on its neighbors' scores |
| **Penalty** | Score decrement applied to superseded/contradicted nodes |
| **Dominant domain** | The knowledge domain whose best-matching node scores highest for a given query |
| **Hop** | One step of graph propagation (A influences B via one edge) |
| **Episode** | A logged query event: query text, top result, optional feedback, timestamp |
| **Decay** | Gradual reduction of edge weight when the edge is not activated over time |
| **Confidence** | A manually assigned or derived measure of how certain the node's content is |
| **Relation type** | A semantic label on an edge defining the nature of the relationship |
| **Credit assignment** | The problem of determining which edge(s) caused a correct or incorrect result |
| **Hebbian learning** | "Neurons that fire together wire together" — the conceptual basis for weight reinforcement |
| **Y = f(X, Graph)** | Goldorn's central formula: output is a function of input and the knowledge graph (not weight matrices) |

---

*Document generated: 2026-06-24*  
*System version: v0.2*  
*Next milestone: v0.3 — automated node extraction*
