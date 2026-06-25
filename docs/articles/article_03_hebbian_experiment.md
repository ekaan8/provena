# Does Hebbian Learning Work in a Knowledge Graph? An Experiment

*Part 3 of 4 in the Provena Research Series*

---

Most claims in AI research arrive with a structural deficit: they are true in the paper and untested in the code.

This article does the opposite. I built the system, ran the measurements, and I am going to report what I found — including the result that contradicted my original hypothesis. That result is the most interesting part.

---

## The Three Claims, Made Explicit

Provena rests on three specific empirical claims. Not "this architecture is promising" or "this approach has potential" — claims with numbers attached.

**Claim 1:** Multi-hop graph traversal with typed relation boost/penalty improves retrieval Precision@3 compared to raw FAISS embedding similarity.

**Claim 2:** Explicit feedback updates edge weights according to a Hebbian rule, and repeated feedback shifts retrieval ranking.

**Claim 3:** The `blame_edge` function correctly identifies the highest-contributing edge in a query traversal path.

Each claim can be tested. Here is what the tests showed.

---

## The System

Before the numbers, the architecture that produced them.

Provena's retrieval pipeline has three stages:

**Stage 1: Semantic candidate retrieval.** The query is embedded using `sentence-transformers`. FAISS finds the 30 most similar nodes in the database using cosine similarity.

**Stage 2: Graph activation.** For each candidate node, the system loads a local subgraph — all edges within 2 hops. It then propagates activation scores through this subgraph using:

```
contribution = source_score × edge_weight × relation_coefficient × domain_coefficient
```

Where `relation_coefficient` varies by edge type:

| Relation | Coefficient |
|---|---|
| `causes` | 1.2 |
| `supports` | 1.1 |
| `example_of` | 1.0 |
| `related_to` | 0.8 |
| `contradicts` | -0.5 (penalty) |
| cross-domain | 0.1 |

**Stage 3: Contradiction resolution.** Nodes making conflicting claims compete. The winner is determined by confidence score → recency → positive feedback count. The loser has its score multiplied by 0.10.

The result is a ranked list of (node, content, confidence, score) tuples.

The **Hebbian learning rule** is:

```python
new_weight = clamp(
    old_weight + (feedback × confidence) − (0.01 × decay_days),
    0.0, 1.0
)
```

Where `feedback` is +1 (reward) or -1 (blame), `confidence` is the source node's reliability score (0.0–1.0), and `decay_days` is the number of days since the edge was last activated.

---

## Experiment 1: Does the Graph Help or Hurt?

**Setup:** I ingested 36 sentences across three knowledge domains (Operating Systems, Machine Learning, Databases — 12 sentences each). I wrote 15 queries — 5 per domain — and measured whether the correct concept appeared in the top-3 results. I ran each query twice: once with raw FAISS only (no graph), once with the full system (FAISS + graph traversal + boost/penalty).

**Metric:** Precision@3 — does the correct concept appear in the top 3 results?

**Results:**

| Domain | Embedding Only | Full System | Δ |
|---|---|---|---|
| Operating Systems | 100% | 100% | 0% |
| Machine Learning | 100% | 100% | 0% |
| Databases | **100%** | **80%** | **−20%** |
| **Overall** | **100%** | **93.3%** | **−6.7%** |

The graph made things worse in one domain and made no difference in the others. This was not the result I expected.

**What happened in Databases?**

Two queries failed under the full system:
- *"How does sharding distribute database load?"* → Top-1 was a NoSQL node rather than the sharding node
- *"What is the purpose of database indexing?"* → Same misdirection

The diagnosis: `auto_topology.py` had generated a weak edge between the NoSQL node and a connection-pooling node (`NoSQL → uses → connection_pooling`). This edge was formally valid — NoSQL systems do use connection pooling — but it created a spurious activation path that boosted the wrong node when the query was about sharding or indexing.

In other words: **the graph traversal amplified a weak relationship into a retrieval error**. The embedding, on its own, would have ignored that relationship entirely.

This is the most important finding of the experiment, and it cuts directly against the intuitive appeal of graph-based retrieval. A graph is not a universal improvement over embeddings. A graph is an *amplifier* — it makes good relationships stronger and bad relationships louder.

The implication is architectural: **graph quality determines retrieval quality**. A knowledge system built on accurate, well-typed relationships outperforms embedding-only retrieval. A system with noisy, opportunistic edges performs worse.

I ran the Databases domain a second time after manually correcting the worst edges, and Precision@3 returned to 100%. This confirms the diagnosis but also confirms that the system's performance is sensitive to edge quality in a way that a pure embedding system is not.

---

## Experiment 2: Do Edge Weights Actually Change?

**Setup:** I ran 10 queries against the benchmark corpus, applied explicit feedback (reward or blame) to each, then re-ran the same 10 queries and measured edge weight changes and ranking shifts.

**Results:**

| Metric | Value |
|---|---|
| Edges modified | 4 out of 49 (8.2%) |
| Average \|Δw\| | 0.3918 |
| Queries with top-1 ranking shift | 0 out of 10 |

**Edge weight changes in detail:**

| Edge | Before | After | Δ | Type |
|---|---|---|---|---|
| `learning_rate → adam_optimizer` | 0.472 | 1.000 | +0.528 | reward ×3 |
| `mutex_locks → thread_creation` | 0.561 | 1.000 | +0.439 | reward ×2 |
| `epoll_efficient → epoll_outperforms` | 0.460 | 0.760 | +0.300 | reward ×1 |
| `acid_properties → transaction` | 0.316 | 0.016 | −0.300 | blame ×1 |

The weights changed. Substantially — an average absolute delta of 0.39 is not a rounding error. The blamed edge dropped from 0.316 to 0.016, effectively removing it from future traversal paths.

But the ranking didn't shift. The top-1 result for all 10 queries was identical before and after feedback.

**Why?**

Two reasons, and both are honest findings rather than failures of the system.

First: **embedding dominance at small scale**. When a corpus has only 36 sentences, the cosine similarity between a query and the single most relevant node is already very high. The graph boost/penalty mechanism operates in addition to the base similarity score. At small scale, the base similarity dominates — the graph can nudge results but rarely overturn them.

Second: **Hebbian learning is a cumulative mechanism, not an instant one**. This is, I think, the more important insight. The Hebbian rule is not designed to change ranking after a single feedback signal. It is designed to gradually strengthen paths that are consistently useful and gradually weaken paths that consistently fail. A single blame signal moves the edge weight from 0.316 to 0.016 — but to actually shift retrieval ranking, that edge would need to have been competitive with the winning edge in the first place.

What this means is that the experiment, while correctly executed, was too short to observe the mechanism's intended effect. Hebbian learning produces its meaningful results over many query-feedback cycles, not after ten. This is not a flaw in the system; it is a correct description of how biological Hebbian learning works. "Cells that fire together wire together" describes a gradual, accumulative process — not an instant rewiring.

For a future experiment: run 100 feedback cycles on the same 10 queries and measure the cumulative effect on edge weights and retrieval ranking over time. My prediction, based on the weight delta magnitudes observed here, is that ranking shifts would become visible by cycle 20-30.

---

## Experiment 3: Does blame_edge Find the Right Edge?

**Setup:** I built a controlled test graph with known edge weights: one edge at 0.9 (high), one at 0.5 (medium), one at 0.4, one at 0.3 (low). I then ran 3 queries where I knew which edge should have the highest contribution, and checked whether `blame_edge` selected that edge.

**Results:**

| Query | Expected Edge | Selected Edge | Correct? |
|---|---|---|---|
| "Why is epoll efficient for web servers?" | `node_a → node_b` (w=0.9) | `node_a → node_b` | ✅ |
| "What makes IO multiplexing efficient?" | `node_a → node_b` (w=0.9) | `node_a → node_b` | ✅ |
| "Problems with select compared to epoll?" | `node_a → node_c` (supersedes) | `node_a → node_c` | ✅ |

**Accuracy: 3/3 = 100%** (in controlled conditions).

`blame_edge` selects the edge with the highest `contribution` score in the traversal path. In a controlled graph where the high-weight edge is also the semantically relevant one, this works perfectly. In a noisier graph, the highest-contribution edge might not always be the most semantically responsible — contribution is a product of edge weight, base similarity, and relation coefficient, and any of these factors could elevate the wrong edge.

This is an important caveat: `blame_edge` accuracy in the wild likely falls below 100%. The controlled experiment establishes that the mechanism works as designed. Real-world performance would require a larger evaluation with ground-truth annotations.

---

## What the Numbers Actually Say

Let me state the findings directly, without optimistic framing:

1. **Graph traversal does not universally improve retrieval.** In two domains with clean edges, it matched embedding performance exactly. In one domain with noisy edges, it reduced performance by 20%. The graph is a precision instrument, not a general improvement.

2. **Hebbian learning measurably changes edge weights** — with average |Δw| = 0.39 after a single feedback cycle. These changes are logged, auditable, and reversible. Whether they eventually shift retrieval ranking requires a longer experiment.

3. **blame_edge correctly identifies the highest-contributing edge** in controlled conditions. This is the system's cleanest result, and the one with the most direct practical value: when a result is wrong, you can ask the system which relationship was most responsible.

---

## The Research Question, Restated

The original question was: *does Hebbian learning on knowledge graph edges produce measurable retrieval improvement?*

The more precise answer, based on these experiments, is: **it produces measurable edge weight change, which is a necessary but not sufficient condition for retrieval improvement**. Retrieval improvement requires larger corpora, more feedback cycles, and higher-quality initial edge structure.

This is not a negative result. It is an accurate characterization of where the mechanism works and where its effects are too small to observe at this scale. This is exactly the kind of finding that makes a research contribution: not "it works," not "it doesn't work," but "here is the specific condition under which it works and here is the condition under which it doesn't."

---

**Reproduce this experiment:** `python benchmarks/benchmark_retrieval.py` in the [Provena repository](https://github.com/yourusername/provena)

*Previous: [Part 2 — Why Cyc and NELL Failed](article_02_cyc_nell_lessons.md)*
*Next: [Part 4 — AI Without Black Boxes](article_04_traceable_knowledge.md)*
