# When Hybrid Search (BM25 + Embeddings) Beats Pure Vector Search for RAG

> For retrieval-augmented generation, when does hybrid search (BM25 plus embeddings) beat pure vector search?

Hybrid search tends to beat pure vector search when BM25 and the dense retriever surface different relevant documents, which is most common in corpora with high vocabulary mismatch between queries and documents [F8][F6]. On aggregate benchmarks the gains can be substantial, but they vary widely by domain, from about +5% to +24% in one second-hand report [F3]. Hybrid adds little when queries already share many words with documents [F4]. It can hurt when one retriever clearly dominates and the other adds noise, or when the fusion is left untuned [F9][F10][F5]. The size of the gain also depends on how scores are fused: tuned weighted combinations outperformed RRF in Elastic's tests [F1][F2]. Every configuration carries extra latency and operational cost [F12][F14][F15].

## Where hybrid wins: complementary retrievers and vocabulary mismatch

The clearest pattern is complementarity. In an independent pgvector + BM25 RRF evaluation on BEIR SciFact, hybrid beat both single retrievers on every metric [F8]. The gain was most pronounced on Recall@100, because the two retrievers found different relevant documents [F8].

At the aggregate level, a 2025 survey reports that hybrid models raise BEIR nDCG@10 from 43.42 (BM25) to 52.59 [F7]. Gains are not uniform across domains, though. A second-hand report of Weaviate's benchmarking (Snowflake Arctic 2.0 embeddings + BM25 with RRF) suggests improvements ranging from about +5% on BEIR SciFact to about +24% on BRIGHT Biology [F3].

One secondary source argues that the commonly cited 26–31% NDCG gain of hybrid over dense-only on aggregate BEIR is driven by domains with high vocabulary mismatch and should not be expected on all corpora [F6]. Treat this as a plausible interpretation rather than an established result.

Elastic's BEIR experiments also showed gains from fusion [F1]:
- RRF fusion raised average NDCG@10 by 1.4% over ELSER alone.
- It raised average NDCG@10 by 18% over BM25 alone.

Note that ELSER is a learned sparse encoder, not a dense embedding model [F1].

## Where hybrid adds little or hurts

**High lexical overlap.** When queries already share many words with documents, the benefit appears small. On the WANDS e-commerce benchmark, RRF reportedly added only +1.7% Mean NDCG over dense-only [F4].

**One retriever dominates.** A diagnostic study argues that fusion hurts when one retriever is decisively better and the other contributes noise [F9]. In that case fusion dilutes the strong signal and demotes documents the better retriever had already surfaced [F9]. In that study's 'Dense-Only' setting, where dense retrieval dominates, BM25+dense fusion reportedly:
- hurt 38–65% of queries;
- produced a net nDCG@10 loss of 0.03 to 0.11 [F10].

The same study reports that SPLADE+dense interpolation hurt 14–41% of queries on six corpora [F10].

A small 32-query benchmark points the same way [F13]:
- Dense alone beat hybrid on semantic queries, apparently because equal-weight RRF let the weak BM25 ranking drag down the dense ranking.
- The semantic subset was only 6 queries, so this is a hint rather than a solid result.

## Fusion method and tuning matter

Whether hybrid beats dense depends heavily on how the two rankings are combined.

**Untuned fusion can lose.** AIMultiple's initial hybrid setup scored MRR 0.390, below its dense-only baseline of 0.410 [F5][F11]. One source attributes this to an untuned fusion weight, but that attribution is only partially supported [F11].

**Tuned weighting can beat RRF.** In Elastic's experiments, a linear weighted score combination tuned with Bayesian optimization on labeled queries reportedly outperformed RRF [F2]:

| Fusion method | Gain over ELSER | Gain over BM25 |
|---|---|---|
| RRF | +1.4% | +18% [F1] |
| Tuned linear combination | +6% | +24% [F2] |

This suggests that equal-weight RRF is a reasonable default but not optimal [F1][F2][F13]. It also implies that realizing the larger gains requires a labeled evaluation set [F2][F12].

## Costs of going hybrid

Hybrid search adds operational overhead [F12]:
- dual inverted and vector indexes;
- two retrieval paths;
- fusion tuning that requires an evaluation set.

**Latency.** In one small benchmark, hybrid RRF raised nDCG@10 only modestly over dense (0.727 vs 0.709) while p50 latency rose from 13 ms to 35 ms [F14]. Adding a cross-encoder reranker on top gave about 0.8% more nDCG at roughly 20x the latency (698 ms), a difference within noise for 32 queries [F14].

The SPAR paper reports a hybrid DPR+BM25 latency of 58 ms/query, even assuming parallel retrieval [F15]. The comparison figure of about 10 ms for DPR alone on HNSW is only partially supported by the quoted text [F15].

## Practical takeaway

Hybrid is most likely to pay off in three situations:
- The corpus and query set have substantial vocabulary mismatch [F6][F3].
- BM25 and the dense retriever retrieve meaningfully different relevant documents [F8].
- You can tune the fusion weights on labeled queries [F2].

Hybrid is least likely to pay off, and may hurt, in these cases:
- Queries and documents already overlap lexically [F4].
- The dense retriever is already decisively stronger [F9][F10].
- Fusion is left at untuned or equal-weight defaults [F5][F13].

In every case, weigh the gain against added latency and indexing cost [F12][F14][F15].

## Limitations

- All evidence measures retrieval quality (NDCG, MRR, recall); none directly measures downstream RAG answer quality, so the effect on generated answers is inferred, not shown.
- Several key figures come second-hand from a single secondary article: Weaviate domain variance, WANDS, AIMultiple, and the 26–31% BEIR interpretation. These are marked partial and should be treated cautiously.
- Elastic's results combine BM25 with ELSER, a learned sparse model, not a dense embedding model. They may not transfer directly to BM25 + dense vector hybrids.
- Elastic's tuned linear fusion was optimized on labeled queries; the evidence does not show how well those weights generalize to unseen query distributions.
- The AIMultiple hybrid-vs-dense result appears twice in the evidence (F5, F11) and is a single data point, not independent confirmation.
- The rahin1301 benchmark (F13, F14) uses only 32 queries, with 6 semantic queries. Its findings are suggestive only, and the reranker difference is within noise.
- The 'Fusion Tax' study's definition of the 'Dense-Only' regime is not detailed in the evidence, so it is unclear how to identify that regime in practice before running experiments.
- There is tension between sources showing consistent RRF gains (Elastic, the SciFact pgvector evaluation) and sources showing equal-weight RRF hurting (Fusion Tax, the small benchmark). The evidence suggests the outcome depends on corpus and query mix rather than resolving the conflict definitively.
- The DPR-alone latency comparison in the SPAR evidence is only partly supported by the quoted text.

## References

- **[F1]** [Improving information retrieval in the Elastic Stack: Hybrid retrieval](https://www.elastic.co/search-labs/blog/improving-information-retrieval-elastic-stack-hybrid): "Reciprocal Rank Fusion increases average NDCG@10 by 1.4% over Elastic Learned Sparse Encoder alone and 18% over BM25 alone."
- **[F2]** [Improving information retrieval in the Elastic Stack: Hybrid retrieval](https://www.elastic.co/search-labs/blog/improving-information-retrieval-elastic-stack-hybrid) *(partially supported)*: "This approach gives a 6% improvement in average NDCG@10 over Elastic Learned Sparse Encoder alone and 24% improvement over BM25 alone."
- **[F3]** [Hybrid Search for RAG: BM25, SPLADE, and Vector Search Combined](https://www.premai.io/blog/hybrid-search-for-rag-bm25-splade-and-vector-search-combined/) *(partially supported)*: "Shows domain variance in hybrid search gains, from +5% on BEIR SciFact to +24% on BRIGHT Biology."
- **[F4]** [Hybrid Search for RAG: BM25, SPLADE, and Vector Search Combined](https://www.premai.io/blog/hybrid-search-for-rag-bm25-splade-and-vector-search-combined/) *(partially supported)*: "On the WANDS e-commerce benchmark, RRF added only +1.7% Mean NDCG over dense-only."
- **[F5]** [Hybrid Search for RAG: BM25, SPLADE, and Vector Search Combined](https://www.premai.io/blog/hybrid-search-for-rag-bm25-splade-and-vector-search-combined/): "AIMultiple's benchmark found that their initial hybrid setup scored MRR 0.390, below their dense-only baseline of 0.410."
- **[F6]** [Hybrid Search for RAG: BM25, SPLADE, and Vector Search Combined](https://www.premai.io/blog/hybrid-search-for-rag-bm25-splade-and-vector-search-combined/) *(partially supported)*: "reflects domains with high vocabulary mismatch, not all corpora."
- **[F7]** [From Retrieval to Generation: Comparing Different Approaches](https://arxiv.org/html/2502.20245v1): "hybrid models improve nDCG@10 scores on BEIR from 43.42 (BM25) to 52.59"
- **[F8]** [GitHub - daen8584-spec/hybrid-search: Hybrid BM25 and vector retrieval on PostgreSQL with pgvector, evaluated on BEIR SciFact · GitHub](https://github.com/daen8584-spec/hybrid-search): "Hybrid search improves on both retrievers on every metric, most clearly in Recall@100, where the two retrievers find different relevant documents."
- **[F9]** [The Fusion Tax: A Diagnostic Analysis of When Hybrid Retrieval Hurts](https://arxiv.org/html/2610.30612v1) *(partially supported)*: "Fusion hurts when one retriever is decisively better and the other contributes noise"
- **[F10]** [The Fusion Tax: A Diagnostic Analysis of When Hybrid Retrieval Hurts](https://arxiv.org/html/2610.30612v1) *(partially supported)*: "In Dense-Only it hurts 38–65% (net -0.03 to -0.11), the mirror image with BM25 as the noise source."
- **[F11]** [Hybrid Search for RAG: BM25, SPLADE, and Vector Search Combined](https://www.premai.io/blog/hybrid-search-for-rag-bm25-splade-and-vector-search-combined/) *(partially supported)*: "their initial hybrid setup scored MRR 0.390, below their dense-only baseline of 0.410."
- **[F12]** [Hybrid Search for RAG: BM25, SPLADE, and Vector Search Combined](https://www.premai.io/blog/hybrid-search-for-rag-bm25-splade-and-vector-search-combined/) *(partially supported)*: "Hybrid search adds real costs: dual indexing (both inverted and vector index), two retrieval paths, and fusion tuning"
- **[F13]** [GitHub - rahin1301/hybrid-retrieval-search: Hybrid BM25 + dense retrieval with RRF fusion and cross-encoder reranking, evaluated on 1,316 hand-labelled relevance judgements · GitHub](https://github.com/rahin1301/hybrid-retrieval-search) *(partially supported)*: "On semantic queries, dense alone beats hybrid. Since RRF weights both retrievers equally, the weak BM25 ranking drags the dense one down."
- **[F14]** [GitHub - rahin1301/hybrid-retrieval-search: Hybrid BM25 + dense retrieval with RRF fusion and cross-encoder reranking, evaluated on 1,316 hand-labelled relevance judgements · GitHub](https://github.com/rahin1301/hybrid-retrieval-search) *(partially supported)*: "Reranking is about 0.8% better on nDCG@10 but roughly 20x slower, and with only 32 queries that difference is within noise."
- **[F15]** [Salient Phrase Aware Dense Retrieval: Can a Dense Retriever Imitate a Sparse One?](https://arxiv.org/pdf/2110.06918) *(partially supported)*: "a hybrid DPR+BM25 retriever has a latency of 58ms assuming DPR and BM25 retrieval can be done in parallel"

---
*2 sub-questions, 1 research round(s), 15/15 findings passed checks, 15 cited. Cost $1.09, 116s.*
