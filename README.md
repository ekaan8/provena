# Provena

> *From "provenance" — because every piece of knowledge knows where it came from.*

**An experimental knowledge graph that learns from feedback and traces its own reasoning.**

Standard LLMs compress knowledge into opaque weight matrices — you cannot ask *why* they returned a specific result, update a single fact without retraining, or trace which relationship caused an error.

Provena investigates an alternative formulation:

```
Standard LLM:   Y = f(X, W)      — W is a frozen, opaque weight matrix
Provena:        Y = f(X, Graph)  — Graph is explicit, inspectable, updatable
```

Knowledge is stored as **nodes** (discrete, sourced facts) connected by **typed, weighted edges**. The graph learns from feedback using a Hebbian rule. When a result is wrong, `blame_edge()` identifies which specific relationship caused it. Every decision is logged.

> **Research status:** This is a research prototype, not a production system. The experiments documented in the [article series](docs/articles/INDEX.md) show where the architecture works, where it doesn't, and why the failures are as informative as the successes.

---

## Why the Name

*Provenance* — the documented origin and chain of custody of a piece of information. In museum curation, an artifact without provenance is considered untrustworthy. In AI systems, most knowledge has no provenance at all: it is distributed anonymously across billions of weight parameters, with no record of origin, timestamp, or update history.

Provena is built around the opposite assumption: **every fact should know where it came from**.

---

## Key Features

| Feature | Description |
|---|---|
| **Semantic Retrieval** | FAISS cosine similarity + node confidence scoring |
| **Multi-hop Activation** | Graph traversal boosts contextually related nodes via typed edge coefficients |
| **Hebbian Learning** | `Δw = feedback × confidence − decay` — edges strengthen with use, weaken without it |
| **Contradiction Resolution** | Conflicting nodes compete; winner determined by confidence → recency → feedback count |
| **blame_edge()** | Identifies which specific edge contributed most to a wrong result |
| **Full Provenance** | Every node carries `source`, `created_at`, `confidence` — immutably |
| **Auto-topology** | Extracts nodes and edges from raw text automatically (Turkish + English) |
| **Distributed Architecture** | `domain_server.py` + `gateway.py` for multi-server semantic routing |
| **Zero cloud dependency** | SQLite + FAISS + sentence-transformers — fully local, no API key needed |

---

## Quick Start

**Requirements:** Python 3.9+

```bash
git clone https://github.com/yourusername/provena.git
cd provena
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Add your first knowledge node
python provena.py add "Epoll is highly efficient for high connection counts." \
  --domain "operating_systems" --source "guide.pdf" --confidence 0.9

# Query the graph
python provena.py ask "Why is epoll efficient?"

# Give feedback — the graph learns
python provena.py feedback reward

# View graph statistics
python provena.py graph
```

---

## CLI Reference

```
python provena.py ask "your question"          Query the knowledge graph
python provena.py ask "..." --hops 3           Deeper graph traversal (default: 2)
python provena.py ask "..." --mode template    Template output, no Ollama required

python provena.py add "fact statement" \
  --domain "Domain Name" \
  --source "source.pdf" \
  --confidence 0.85                            Add a knowledge node

python provena.py import path/to/file.txt \
  --domain "domain_hint"                       Import text, auto-extract nodes + edges

python provena.py feedback reward              Reward last query's active path
python provena.py feedback blame               Penalize last query's active path

python provena.py graph                        Graph statistics
python provena.py history                      Recent query episodes
python provena.py domains                      Domain distribution
```

---

## Architecture

```
Raw Text / User Input
       │
  auto_topology.py
  (sentence split → knowledge claim filter → embedding → node/edge extraction)
       │
  knowledge_graph.py
  (SQLite node/edge storage + FAISS embedding index)
       │
  Query: FAISS → candidate nodes → load_active_subgraph()
       │
  Multi-hop activation:
    contribution = source_score × edge_weight × relation_coef × domain_coef
       │
  resolve_contradictions() → winner by confidence → recency → feedback
       │
  blame_edge() ← which edge caused this result?
       │
  update_weight() ← Δw = feedback × confidence − decay
       │
  Output: ranked (node_id, content, confidence, score)
       │
  [Optional] Ollama NL generation
       │
  [Distributed] domain_server.py → gateway.py → semantic routing
```

### Relation Type Coefficients

| Relation | Coefficient | Effect |
|---|---|---|
| `causes` | 1.2 | Strong boost |
| `supports` | 1.1 | Moderate boost |
| `example_of` | 1.0 | Neutral |
| `related_to` | 0.8 | Mild boost |
| `contradicts` | −0.5 | Penalty |
| cross-domain | 0.1 | Strong isolation |

---

## How Hebbian Learning Works

```python
# Δw = feedback × confidence − (0.01 × decay_days)
new_weight = clamp(
    old_weight + (feedback × confidence) − (0.01 × decay_days),
    min=0.0, max=1.0
)
# feedback: +1 (reward), -1 (blame)
# confidence: source node reliability (0.0–1.0)
# decay: time-based forgetting (0.01 per day since last activation)
```

Rewarded edges strengthen. Blamed edges weaken. Edges that are never used slowly decay toward 0.

Every weight change is logged: which edge, what the contribution was, what the weight was before and after, and why.

---

## Distributed Mode

```bash
# Start domain servers (each with its own database)
python domain_server.py --port 8001 --db os_knowledge.db
python domain_server.py --port 8002 --db ml_knowledge.db

# Route queries through the gateway
python gateway.py ask "What makes epoll efficient?" \
  --servers http://localhost:8001 http://localhost:8002
```

The gateway embeds the query, computes cosine similarity with each server's domain profile, and routes to the most relevant server(s). Cross-domain queries trigger broadcast with result merging.

---

## Running the Benchmark

```bash
python benchmarks/benchmark_retrieval.py
```

This runs three experiments on an isolated benchmark database (production data untouched):

1. **Graph vs. Embedding:** Does graph traversal improve Precision@3?
2. **Hebbian Learning:** Do edge weights change after feedback, and does ranking shift?
3. **blame_edge:** Does credit assignment identify the right edge?

Results are saved to `benchmarks/results/benchmark_report.md`.

---

## Running Tests

```bash
cd tests
python test_v08_features.py    # Distributed architecture integration test
python test_auto_features.py   # auto_topology extraction test
```

---

## What the Experiments Found

Full details in the [article series](docs/articles/INDEX.md). Short version:

| Experiment | Result |
|---|---|
| Graph vs Embedding (OS domain) | 100% P@3 — graph matched embedding exactly |
| Graph vs Embedding (DB domain) | 80% P@3 — graph **hurt** performance due to noisy edges |
| Hebbian learning \|Δw\| | 0.3918 average absolute weight change per feedback cycle |
| blame_edge accuracy | 100% (3/3) on controlled graph |

The most important finding: **the graph amplifies the quality of its edges**. Good edges improve retrieval. Poor edges reduce it. This is more informative than a system that always improves, because it identifies the real bottleneck: knowledge quality, not retrieval mechanics.

---

## Article Series

This project is documented in a 4-part research series:

| Article | Title | Read |
|---|---|---|
| Part 1 | Why AI Forgets — The Case for Explicit Knowledge | [→](docs/articles/article_01_why_ai_forgets.md) |
| Part 2 | The Graveyard of Knowledge Systems — What Cyc and NELL Got Wrong | [→](docs/articles/article_02_cyc_nell_lessons.md) |
| Part 3 | Does Hebbian Learning Work in a Knowledge Graph? An Experiment | [→](docs/articles/article_03_hebbian_experiment.md) |
| Part 4 | AI Without Black Boxes — The Case for Traceable Knowledge | [→](docs/articles/article_04_traceable_knowledge.md) |

---

## File Structure

```
provena/
├── provena.py           ← CLI entry point
├── knowledge_graph.py   ← Core engine: FAISS, SQLite, Hebbian learning
├── auto_topology.py     ← Auto node/edge extraction from raw text
├── gateway.py           ← Distributed semantic routing
├── domain_server.py     ← HTTP API for a single knowledge domain
├── ingest_data.py       ← File import helper
├── seed.py              ← Example data population
├── requirements.txt
├── .gitignore
├── benchmarks/
│   ├── benchmark_retrieval.py   ← Reproduces all three experiments
│   └── results/
│       ├── benchmark_report.md
│       └── benchmark_results.json
├── data/sample_texts/           ← Benchmark corpus (3 domains × 12 sentences)
├── tests/
│   ├── test_v08_features.py
│   └── test_auto_features.py
└── docs/
    ├── articles/                ← 4-part research series
    ├── history/                 ← Development logs
    ├── vision/                  ← Original architecture vision documents
    └── references/              ← Research papers and notes
```

---

## Current Status (v0.8)

**What is verified:**
- Semantic retrieval with FAISS works correctly
- Multi-hop graph traversal affects retrieval scores (for better or worse, depending on edge quality)
- Hebbian updates produce measurable weight changes (avg |Δw| = 0.39 per cycle)
- Contradiction resolution picks winners by confidence → recency → feedback
- blame_edge correctly identifies highest-contributing edge (controlled conditions)
- auto_topology correctly extracts Turkish and English knowledge claims

**Known limitations:**
- ~36 sentences in the benchmark corpus — not a scale test
- Ranking shifts from Hebbian learning require multiple feedback cycles to become visible
- No authentication on domain servers
- No web UI

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Provena — explicit knowledge, learnable graph, traceable reasoning.*
*Every fact knows where it came from.*
