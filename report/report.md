# FastAPI Documentation RAG Chatbot Report

## Overview

This project implements a Retrieval-Augmented Generation chatbot over FastAPI documentation. It connects document ingestion, token-aware chunking, dense vector search with Chroma, and grounded LLM generation with source citations.

## Architecture

See `report/architecture_diagram.md` for the pipeline diagram.

The pipeline has these stages:

1. Load HTML and Markdown documents.
2. Normalize metadata: `source`, `source_id`, `citation_id`, `title`, `filename`, `doc_type`, and `date`.
3. Split documents into token-aware chunks.
4. Embed chunks with `sentence-transformers/all-MiniLM-L6-v2`.
5. Store vectors, text, metadata, and chunk indexes in Chroma.
6. Retrieve top-k chunks for a user query.
7. Generate an answer from retrieved context only.
8. Validate citations against retrieved citation IDs.
9. Display answer, citations, and evidence in Streamlit.

## Corpus and Ingestion

The corpus currently includes two file types in practice:

- 61 HTML documents from locally scraped FastAPI documentation.
- 12 Markdown documents derived from local official FastAPI HTML pages.

Date metadata is attempted from document metadata/frontmatter. When no date is available, the pipeline stores `"None"` because Chroma metadata does not accept Python `None`.

## Chunking

The project implements two token-aware strategies:

- Fixed token windows with overlap.
- Sentence/paragraph-aware recursive splitting measured with token counts.

Assignment constraints are enforced:

- Minimum chunk size parameter: 100 tokens.
- Maximum chunk size parameter: 512 tokens.
- Overlap must be 10-25% of chunk size.

Full evaluation-set chunking comparison:

| Strategy | Chunk count | Precision@5 | Recall@5 |
|---|---:|---:|---:|
| Fixed token | 874 | 0.573 | 0.900 |
| Semantic token | 871 | 0.547 | 0.867 |

The final index uses fixed token chunks with `chunk_size=256` and `overlap=50`.

## Evaluation

The QA dataset contains 31 questions:

- 30 supported FastAPI questions.
- 1 unsupported refusal question.

Each supported item includes a reference answer, source ID, and ground-truth source passages.

Latest retrieval-only metrics:

- Precision@5: 0.573
- Recall@5: 0.900
- Answer relevance proxy: 0.788

Generation metrics and refusal accuracy were not computed in the saved lightweight run because that requires an LLM API call. The evaluator supports `--generation` for API-backed generation proxies.

## Experiments

See `report/experiment_summary.md` and `eval/experiment_log.csv`.

The most important design change was switching from semantic token splitting to fixed token splitting because fixed chunks achieved better Precision@5 and Recall@5 on the full QA dataset.

## GPT-2 vs BERT

See `report/gpt2_vs_bert.md`.

The short version: BERT-style encoders are used for retrieval because they produce semantic vector representations. GPT-style decoders are used for generation because causal language modeling is designed for fluent text continuation.

## Limitations

See `report/failure_modes.md`.

Main limitations are imperfect retrieval precision, retrieval-only saved generation metrics, derived Markdown rather than separate upstream Markdown crawl, tokenizer fallback behavior, and lightweight citation validation.

## Reflection and Future Work

With more time, I would add a reranker, run full RAGAS with an evaluator LLM, expand unsupported queries, fetch upstream Markdown directly from the FastAPI repository, and tune retrieval with hybrid BM25 + dense search.
