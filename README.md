# FastAPI Docs RAG Chatbot

Retrieval-Augmented Generation chatbot over FastAPI documentation. The project includes ingestion, token-aware chunking, sentence-transformer embeddings, Chroma retrieval, grounded LLM generation with citations, Streamlit UI, and evaluation artifacts.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your `GROQ_API_KEY` to `.env` for generation/UI. Retrieval-only evaluation does not call the LLM API.

The embedding model is `sentence-transformers/all-MiniLM-L6-v2`. The first run may download model files from HuggingFace. Later runs use the local cache; if the model is missing and there is no internet, index building will fail with a clear message.

## Data

The corpus uses two file types in practice:

- `data/raw/html/`: locally scraped FastAPI HTML pages
- `data/raw/markdown/`: Markdown documents derived from the local official FastAPI HTML pages

Unavailable document dates are stored as the literal metadata value `"None"` because Chroma does not accept Python `None` values in metadata.

## Commands

```bash
# Optional: scrape/update local HTML pages
python ingest/scraper.py

# Build Markdown corpus from local HTML pages
python scripts/make_markdown_corpus.py

# Build the selected production index
python scripts/build_index.py --strategy fixed --chunk-size 256 --overlap 50

# Compare chunking strategies on the full QA dataset
python scripts/compare_chunking.py

# Enrich QA data with source passages
python eval/enrich_qa_dataset.py

# Retrieval-only evaluation
python eval/run_eval.py --top-k 5

# Optional LLM generation evaluation
python eval/run_eval.py --top-k 5 --generation

# Run real experiments with index rebuilds where needed
python eval/run_experiments.py

# Start UI
streamlit run ui/app.py
```

## Current Measured Results

Latest retrieval-only run with fixed token chunks:

- Precision@5: `0.573`
- Recall@5: `0.900`
- Answer relevance proxy: `0.788`
- Generation/RAGAS metrics: not run in the saved lightweight evaluation; run with `--generation` and API access for generation proxies.

Chunking comparison on the full evaluation set:

- Fixed token chunks: P@5 `0.573`, R@5 `0.900`
- Semantic token chunks: P@5 `0.547`, R@5 `0.867`

The production index uses fixed token chunking because it performed better on the current evaluation set.

## Architecture

1. Ingestion loads HTML and Markdown into a shared `Document` schema.
2. Metadata is normalized with `source`, `source_id`, `citation_id`, `title`, `filename`, `doc_type`, and `date`.
3. Token-aware chunking creates fixed or semantic chunks within the 100-512 token assignment range.
4. `all-MiniLM-L6-v2` embeds chunks.
5. Chroma stores vectors, chunk text, and metadata.
6. Retrieval returns top-k chunks by cosine similarity.
7. The generator answers only from retrieved context and validates citations against retrieved `citation_id` values.
8. Streamlit displays answers, citations, source links, and retrieved evidence.

## Evaluation Dataset Schema

Each QA item in `eval/qa_dataset.json` includes:

- `question`
- `ground_truth`
- `reference_answer`
- `source`
- `source_id`
- `ground_truth_passages`
- `expected_refusal`

Generated evaluation files:

- `eval/metrics_summary.json`
- `eval/retrieval_results.json`
- `eval/ragas_results.json`
- `eval/experiment_log.csv`
- `eval/chunking_comparison.json`
