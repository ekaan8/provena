# Why AI Forgets — And Why That Might Be By Design

*Part 1 of 4 in the Provena Research Series*

---

Ask ChatGPT when it was trained and it will tell you. Ask it to name a news event from last week and it will confabulate. Ask it *why* it said something and it will give you a confident, structurally plausible, and often completely made-up explanation of its own reasoning.

This is not a bug being fixed in the next version. It is the logical consequence of a fundamental architectural decision made decades ago, inherited by every major language model today.

The decision: **knowledge should live inside weights**.

---

## The Weight Matrix as a Filing System

When a language model is trained, it reads billions of text documents and distills them into a fixed set of numerical parameters — billions of floating-point numbers arranged in matrices. This is the model's "memory." When you ask it a question, it doesn't look anything up. It runs your input through a mathematical function that transforms tokens into predictions using those frozen weights.

This is astonishingly effective. The compression is so dense that a 70-billion-parameter model can reproduce the gist of millions of documents with impressive fidelity.

But something is lost in that compression. The provenance. The timestamp. The source. The ability to correct a single fact without touching everything else.

The standard formulation is:

```
Y = f(X, W)
```

Where `X` is your query and `W` is the weight matrix — the compressed, static, opaque record of everything the model was trained on. To change one fact in `W`, you must retrain, or fine-tune, which risks corrupting adjacent facts. The model does not know which weights encode which knowledge. Neither do we.

---

## The Specific Cost of Opacity

Let's make this concrete. Suppose a medical AI system trained on clinical literature says:

> "Drug A is safe for patients with condition B."

And suppose that six months after training, a major study reverses this finding. The system now has a dangerous, outdated belief baked into its weights. There is no surgical fix. You cannot reach into the weight matrix and update the one parameter that encodes this fact. You must retrain the entire model, or add a retrieval layer on top, or rely on prompt engineering to override the wrong answer.

None of these solutions are clean. All of them are symptoms of the same root problem: **the fact and the system that stores the fact are merged into the same artifact**.

There is an older way of thinking about this problem. In 1965, Ted Nelson began sketching Xanadu — a vision of hypertext where every piece of information would carry its origin, its connections, its version history. Not a document, but a living node in a web of traceable relationships. He was describing, in the context of human documents, exactly what AI systems fail to provide about their own knowledge: the answer to "where did this come from and is it still true?"

---

## An Alternative Formulation

What if instead of:

```
Y = f(X, W)
```

we tried:

```
Y = f(X, Graph)
```

Where `Graph` is not a monolithic weight matrix but an explicit network of **discrete knowledge units** — nodes — connected by **typed, weighted relationships** — edges. Each node carries its content, its source, its timestamp, its confidence score. Each edge carries its type (`supports`, `contradicts`, `causes`, `supersedes`), its weight, and its update history.

This is not a new idea in isolation. Knowledge graphs have existed since the 1960s. What is new — and what remains surprisingly unstudied — is whether such a graph can *learn* from feedback over time in a way that meaningfully improves retrieval. Not through gradient descent and backpropagation over a global loss function, but through local, edge-level updates triggered by explicit signals.

This is the question Provena is built to investigate.

---

## What "Learning" Means Here

In a weight-based model, learning happens during training: you show the model billions of examples, it adjusts its weights to minimize a loss function, and then it stops. Fine-tuning adjusts the weights again on new data, but the process is expensive and risks catastrophic forgetting — the phenomenon where the model loses old knowledge while acquiring new.

In Provena's formulation, learning is different. It is local, edge-level, and feedback-driven. The update rule is:

```
Δw = η × feedback × confidence − (0.01 × days_since_use)
```

Where:
- `feedback` is +1 (this answer was correct) or -1 (this answer was wrong)
- `confidence` is the reliability score of the source node
- The decay term means relationships that are never reinforced gradually weaken

This is, deliberately, a Hebbian rule. "Neurons that fire together wire together." But applied not to synapses in a neural network, but to edges between knowledge units in a graph.

The hypothesis is that a graph updated by this rule will, over time, produce better retrieval results than a static graph — and that this improvement will be *visible*, *traceable*, and *reversible* in a way that weight updates in a neural network are not.

---

## What This Gives You That Weights Do Not

Three things, specifically.

**First: provenance.** Every node in Provena's graph carries `source`, `created_at`, and `confidence`. When the system returns a result, you can ask "where did this come from?" and get a real answer — not a probability distribution, but a specific source text and timestamp.

**Second: surgical update.** When a fact changes, you update the node. Adjacent relationships are unaffected unless you explicitly change them. There is no risk of corrupting unrelated knowledge.

**Third: error attribution.** When the system returns a wrong answer, a mechanism called `blame_edge` traces which specific relationship contributed most to the incorrect result. This is credit assignment at the edge level — something weight-based systems cannot provide without post-hoc approximation tools like LIME or SHAP.

---

## A Modest Claim and a Real Question

Provena is not a language model replacement. It cannot write poetry or summarize documents with the fluency of GPT-4. What it can do is demonstrate, on a small but measurable scale, that the alternative formulation `Y = f(X, Graph)` produces a system with properties that `Y = f(X, W)` structurally cannot:

- **Inspectable reasoning paths**
- **Updateable individual facts**
- **Feedback-driven edge learning**
- **Source-traced retrieval**

Whether these properties can be preserved at scale — whether a graph-based system can eventually approach the retrieval quality of an embedding model on large corpora — is an open question. But it is a question worth asking, and asking with working code and real measurements.

In the next article, I look at what happened to the two previous large-scale attempts to answer a similar question — Cyc and NELL — and what Provena is doing differently.

---

**The Provena source code is available at:** [github.com/yourusername/provena](https://github.com)

*Next: [Part 2 — Why Cyc and NELL Failed, And What We Learned From Them](article_02_cyc_nell_lessons.md)*
