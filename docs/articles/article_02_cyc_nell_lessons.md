# The Graveyard of Knowledge Systems — What Cyc and NELL Got Wrong

*Part 2 of 4 in the Provena Research Series*

---

In 1984, a researcher named Doug Lenat made a bet. He believed that if you gave a computer enough common-sense knowledge — the kind of facts that humans know but no one writes down — it would eventually become intelligent. He called the project Cyc, short for *encyclopedia*. He estimated it would take a few hundred person-years to complete.

Forty years later, Cyc still exists, still maintained by a small company, still incomplete. By some estimates, it contains over 25 million rules and facts, added mostly by hand, mostly by experts, over four decades of labor.

It is the most ambitious knowledge engineering project in the history of AI — and it serves primarily as a cautionary tale.

What went wrong is not obvious, and the lessons are not the ones usually cited.

---

## Cyc: The Problem Was Not the Idea

The common narrative about Cyc is that symbolic AI was simply wrong — that the future belongs to neural networks and statistical learning, and that Cyc was a relic of a mistaken paradigm.

This is too easy. The deeper problem was not symbolic representation. It was **the assumption that breadth could substitute for depth**.

Cyc tried to capture everything. *Every* common-sense fact about the world. A dog is a mammal. Dogs can bark. Barking is louder than whispering. Whispering is quieter than speaking. Speaking can express ideas. Ideas can be communicated. Communication requires shared context. Shared context assumes background knowledge...

The dependency chain never ends. Every fact you add reveals ten more gaps. Lenat called this the "long tail of common sense" — the observation that the distribution of facts needed for general intelligence has no natural stopping point. For every thousand obvious facts you encode, another thousand edge cases emerge.

This was not a failure of will or resources. It was a structural problem: **the domain of general human knowledge is not enumerable by humans working faster**.

---

## NELL: When the Internet Was the Database

Twenty years after Cyc began, a team at Carnegie Mellon University tried a different approach. They called it NELL — Never-Ending Language Learner. Instead of encoding knowledge by hand, NELL would learn from the web, continuously, from 2010 onward.

The premise was elegant: the internet contains billions of sentences stating facts about the world. If you can extract those facts reliably enough, you end up with a knowledge base that grows without human labor.

NELL ran for eight years. It extracted hundreds of millions of beliefs from web text. And then it quietly stopped producing useful output, for a reason that is more important than its proponents usually admit.

**Noise compounds faster than signal when the source is uncontrolled.**

The web contains truths and falsehoods in roughly equal abundance, and no consistent structure to distinguish them. NELL extracted facts like "Jimi Hendrix is an athlete" because some page somewhere described him as an "athletic performer." It extracted country capitals from satirical articles, disease symptoms from conspiracy sites, and corporate information from outdated press releases.

Each wrong fact polluted the graph. Edges connected incorrect nodes. Subsequent inferences propagated the errors. By the time the system had run long enough to accumulate meaningful coverage, it had also accumulated enough corrupted connections to make the whole graph unreliable.

NELL's failure was not a failure of extraction — the NLP was impressive for its era. It was a failure of **quality control at scale**. The system had no principled way to decide which sources to trust, no mechanism to detect when an extracted fact was contradicted by its own existing beliefs, and no way to roll back corruption without discarding everything.

---

## The Deeper Pattern

Looking at Cyc and NELL side by side, a pattern emerges that the AI community often acknowledges in theory but underestimates in practice:

**The knowledge acquisition bottleneck is not a resource problem. It is a representation and validation problem.**

Cyc had the resources — decades of expert labor. NELL had the data — billions of web documents. Neither had a principled answer to the question: *when is a knowledge claim reliable enough to store permanently, and how do you update the claim when the world changes?*

Both systems treated knowledge as a corpus to accumulate. Neither built a mechanism to continuously re-evaluate what was already stored. Cyc's rules became increasingly difficult to modify without breaking downstream dependencies. NELL's graph became a palimpsest — a surface written over so many times that the original text is illegible.

---

## What Provena Does Differently — And Honestly

I want to be careful not to overclaim here. Provena is a research prototype with 25 nodes. Cyc has 25 million rules. The comparison is not a competition.

But the architectural differences are real, and they address the specific failure modes of both systems.

**Against Cyc's bottleneck:** Provena uses `auto_topology.py` to extract nodes and edges from raw text automatically, using embeddings and linguistic heuristics rather than manual encoding. Knowledge acquisition does not require human experts. The cost of adding a new knowledge claim is approximately zero marginal human labor.

**Against NELL's noise problem:** Every node enters Provena with an initial confidence score below 1.0. The system has a `resolve_contradictions()` function that detects when two nodes make conflicting claims and reduces the confidence of the losing node. New knowledge doesn't simply pile on — it is checked against existing beliefs before storage.

**Against both systems' stasis:** Edge weights in Provena change over time. Edges that are repeatedly traversed in successful queries get stronger. Edges that lead to poor results and explicit `blame` feedback get weaker. A fact that was once useful but is never invoked again gradually decays. The graph does not accumulate corruption — it gradually down-weights it.

This is not a solution to the general knowledge acquisition problem. It is a targeted response to specific failure modes, tested on a small scale, with all the caveats that implies.

The question this raises — which the benchmark in Part 3 attempts to answer — is whether these mechanisms produce *measurable improvement* over a static baseline, even at small scale. If they do, the argument for this architecture becomes empirical rather than theoretical.

---

## The Lesson From the Graveyard

Cyc and NELL failed at the hardest possible version of their respective problems. Cyc tried to capture all human knowledge manually. NELL tried to extract all web knowledge automatically. Both were attempting to build the ocean, not the harbor.

The more productive question — and the one that Provena is actually exploring — is smaller and more tractable:

*Can a knowledge graph that learns from feedback outperform a static knowledge graph on a specific, constrained retrieval task? And if so, by how much, and under what conditions?*

This question has a measurable answer. And a measurable answer, even a modest one, is more valuable than an ambitious answer that cannot be verified.

The graveyard of AI knowledge systems is full of systems that tried to be infinite. What the field might actually need is a system that is finite, explicit, and honest about what it does not know.

---

**The Provena source code is available at:** [github.com/ekaan8/provena](https://github.com)

*Previous: [Part 1 — Why AI Forgets](article_01_why_ai_forgets.md)*
*Next: [Part 3 — Does Hebbian Learning Work in a Knowledge Graph?](article_03_hebbian_experiment.md)*
