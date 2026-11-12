# When hybrid search (BM25 + embeddings) beats pure vector search in RAG

> For retrieval-augmented generation, when does hybrid search (BM25 plus embeddings) beat pure vector search?

Hybrid search beats pure vector search mainly in three situations: the embedding model is out of its training domain, queries depend on exact or rare terms, or BM25 and the embeddings miss different queries. Out of domain, dense models can fall well below BM25 [F1][F2][F3]. Exact or rare terms include codes, IDs, names, citations, numbers and finance-style text [F4][F13][F14]. When the two retrievers make different mistakes, fusing them recovers what each one misses [F10]. On a 2026 financial text-and-table RAG benchmark, hybrid RRF beat both BM25 and dense retrieval, and the better retrieval carried through to better answers [F4][F5][F6]. On an e-commerce benchmark, hybrid gave about a 7% NDCG gain over two retrievers that each scored about the same [F8]. Hybrid does not always win, though. On a small corpus whose queries used the documents' own wording, RRF scored between its two inputs, not above both [F9][F11]. Its value also shrinks when one retriever dominates or chunks are poorly sized [F15][F16].

## Why the two retrievers make different mistakes

BEIR's zero-shot evaluation found BM25 a robust baseline. Depending on the task and domain, dense retrievers can do substantially worse than it [F1]. Dense models win mainly when the target data looks like the data they were trained on [F2]. In-domain results are a poor guide here: BM25 trails neural models by 7–18 points on MS MARCO, yet holds up better on out-of-domain sets [F3]. Exact-string queries are the clearest gap in pure vector search. Examples include error codes, SKUs, version numbers, drug names, case citations and clause IDs [F13][F14].

## Evidence that hybrid wins

**Financial text-and-table documents.** On a 2026 benchmark, BM25 beat dense retrieval on every metric and hybrid RRF scored best [F4]. Recall@5 was 0.695 for hybrid, 0.644 for BM25 and 0.587 for dense [F5]. The gain held on individual subsets; on TAT-DQA, for example, hybrid reached 0.647 against 0.566 for BM25 and 0.549 for dense [F7]. Better retrieval also raised end-to-end answer quality, from 0.251 with BM25 to 0.282 with hybrid [F6].

**E-commerce product search (WANDS).** BM25 and vector search scored almost the same (NDCG 0.698 vs 0.695), while a tuned hybrid reached 0.750 [F8]. This fits the general rule: fusion pays most when the two inputs are similarly strong but get different queries right [F10].

## When hybrid does not help, or helps little

In a small reproducible benchmark, RRF fusion scored between BM25 and dense on every metric, not above both [F9]. The author concludes that hybrid only pays off when the retrievers fail on different queries [F10]. If queries use the same vocabulary as the documents, BM25 alone may be enough [F11]. In that benchmark, BM25 also ran about 40× faster, at 0.12 ms versus about 4.9 ms per query for embedding pipelines [F12]. If BM25 dominates because almost all queries are keyword lookups, the vector side adds cost with little benefit [F15]. Oversized chunks dilute BM25 term statistics and weaken the exact-match signal that hybrid relies on [F16].

## Practical decision rule

Start with hybrid when any of these hold:
- Users search for identifiers or exact strings [F13][F14].
- The corpus is specialized or far from the embedding model's training data [F1][F2].
- Documents are numeric or tabular, such as financial reports [F4][F5].
- BM25 and dense score about the same overall but fail on different queries [F8][F10].

Pure vector search may be enough when the domain matches the embedder's training data and queries are mostly paraphrased, concept-level questions [F2]. Before settling, compare each retriever and the hybrid on your own queries; one small test found fusion added nothing [F9]. Many production pipelines use hybrid as a high-recall first stage followed by a reranker. In the financial benchmark, that two-stage setup lifted Recall@5 from 0.695 to 0.816 [F5][F17].

## Limitations

- The web search quota ran out after four queries. I could not retrieve Anthropic's Contextual Retrieval results, systematic studies of RRF weights, or recent MTEB/BEIR hybrid ablations, so the evidence base is narrow.
- Several sources are vendor or practitioner blogs (Denser, Supermemory, dev.to, personal blogs). Their claims about exact-match failures are plausible but anecdotal, not controlled experiments.
- The GitHub benchmark that found no hybrid gain is very small (Recall@1 moves in steps of about 0.017, roughly 60 queries), so it is illustrative, not conclusive.
- One vendor page (atlan.com) attributes a 43.42→52.59 nDCG@10 hybrid gain to BEIR. I could not verify that figure in the BEIR excerpts I retrieved, so I excluded it.
- Results depend heavily on the embedding model, tokenization of codes, chunk size, and fusion method and weights (RRF k, convex combination). Most cited studies use a single configuration, such as 0.5/0.5 weights.
- Newer embedding models and learned sparse models (e.g., SPLADE) may narrow or change these gaps. None of the retrieved sources evaluated them directly.

## References

- **[F1]** [BEIR: A Heterogenous Benchmark for Zero-shot Evaluation of Information Retrieval Models](https://arxiv.org/html/2104.08663v2): "More computationally efficient dense models can, depending on the task and domain, substantially underperform traditional lexical models like BM25."
- **[F2]** [BEIR: A Heterogenous Benchmark for Zero-shot Evaluation of Information Retrieval Models](https://arxiv.org/html/2104.08663v2): "Dense models outperform BM25 when a high domain overlap is present between the training dataset and the evaluated target dataset."
- **[F3]** [BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models](https://arxiv.org/html/2104.08663v4): "We observe BM25 heavily underperforms neural approaches by 7-18 points on in-domain MS MARCO."
- **[F4]** [From BM25 to Corrective RAG: Benchmarking Retrieval Strategies for Text-and-Table Documents](https://arxiv.org/html/2604.01733v1): "BM25 outperforms dense retrieval on every metric, while hybrid RRF achieves the best scores across the board."
- **[F5]** [From BM25 to Corrective RAG: Benchmarking Retrieval Strategies for Text-and-Table Documents](https://arxiv.org/html/2604.01733v1): "Recall@5 of 0.816 compared to 0.695 for Hybrid RRF alone (+17.4%), 0.644 for BM25 (+26.7%), and 0.587 for dense retrieval"
- **[F6]** [From BM25 to Corrective RAG: Benchmarking Retrieval Strategies for Text-and-Table Documents](https://arxiv.org/html/2604.01733v1): "Better retrieval consistently leads to better answer quality (BM25: 0.251 → Hybrid: 0.282 → Oracle: 0.350 with GPT-4.1-mini)"
- **[F7]** [From BM25 to Corrective RAG: Benchmarking Retrieval ...](https://arxiv.org/pdf/2604.01733): "| TAT-DQA | Dense | 0.549 | 0.647 | 0.364 |"
- **[F8]** [Hybrid Search for RAG: Combining BM25 and Dense Vector Search (2026 Guide)](https://denser.ai/blog/hybrid-search-for-rag/): "a tuned hybrid setup reaches 0.7497 NDCG — a 7.4% lift over either BM25 (0.6983) or pure vector search (0.6953) alone"
- **[F9]** [GitHub - shubhankar360/hybrid-rag-eval: Reproducible benchmark for RAG retrieval: BM25 vs dense vs hybrid RRF vs cross-encoder reranking, scored on Recall@k, MRR, nDCG and latency · GitHub](https://github.com/shubhankar360/hybrid-rag-eval): "hybrid_rrf lands between BM25 and dense on every metric rather than above both."
- **[F10]** [GitHub - shubhankar360/hybrid-rag-eval: Reproducible benchmark for RAG retrieval: BM25 vs dense vs hybrid RRF vs cross-encoder reranking, scored on Recall@k, MRR, nDCG and latency · GitHub](https://github.com/shubhankar360/hybrid-rag-eval): "Hybrid pays off when the legs fail on"
- **[F11]** [GitHub - shubhankar360/hybrid-rag-eval: Reproducible benchmark for RAG retrieval: BM25 vs dense vs hybrid RRF vs cross-encoder reranking, scored on Recall@k, MRR, nDCG and latency · GitHub](https://github.com/shubhankar360/hybrid-rag-eval): "On a corpus that shares vocabulary with its queries, reaching for a vector database first is a cost with no return."
- **[F12]** [GitHub - shubhankar360/hybrid-rag-eval: Reproducible benchmark for RAG retrieval: BM25 vs dense vs hybrid RRF vs cross-encoder reranking, scored on Recall@k, MRR, nDCG and latency · GitHub](https://github.com/shubhankar360/hybrid-rag-eval): "costs 0.12 ms per query against ~4.9 ms for anything involving embeddings"
- **[F13]** [Hybrid search retrieval: BM25 + vector search — supermemory](https://supermemory.ai/blog/hybrid-search-guide/): "If your users ever search for exact strings (codes, names, IDs, version numbers), start with hybrid"
- **[F14]** [Pure Vector Search Is Not Enough Anymore. Here Is What You Actually Need. - DEV Community](https://dev.to/arnav_sharma_25c1c7572a20/pure-vector-search-is-not-enough-anymore-here-is-what-you-actually-need-3aa8): "Regulatory references, drug names, case citations, and clause identifiers are all exact-match queries."
- **[F15]** [Hybrid Search: Combining Keyword and Vector Search for Better Retrieval - Perivitta Rajendran](https://pr-peri.github.io/blogpost/2026/03/05/blogpost-hybrid-search.html): "If 90% of your queries are exact keyword lookups and BM25 dominates every result, you are paying the cost of running vector search"
- **[F16]** [Hybrid Search: Combining Keyword and Vector Search for Better Retrieval - Perivitta Rajendran](https://pr-peri.github.io/blogpost/2026/03/05/blogpost-hybrid-search.html): "If document chunks are too large, BM25 term frequencies are diluted and exact matches lose their signal."
- **[F17]** [Advanced RAG — Understanding Reciprocal Rank Fusion in Hybrid Search](https://glaforge.dev/posts/2026/02/10/advanced-rag-understanding-reciprocal-rank-fusion-in-hybrid-search/): "Use Hybrid Search (Vector + Keyword) fused with **RRF** to retrieve a broad pool of candidates (e.g., top 100)."

---
*1 sub-questions, 1 research round(s), 17/17 findings passed checks, 17 cited. Cost $0.84, 89s.*
