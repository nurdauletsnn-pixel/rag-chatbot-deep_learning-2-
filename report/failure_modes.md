# Limitations and Failure Modes

1. Retrieval sometimes returns neighboring documentation pages. For broad concepts such as metadata, testing, or bigger applications, related pages can outrank the exact page, reducing Precision@5 even when Recall@5 remains high.

2. The current saved evaluation is retrieval-only. Generation metrics and refusal accuracy require an API call with `--generation`; the saved `ragas_results.json` therefore records an honest lightweight equivalent rather than a full RAGAS run.

3. Markdown files are derived from locally scraped official FastAPI HTML pages. This satisfies the two-file-type pipeline in practice, but it is not a separate upstream crawl of the FastAPI GitHub Markdown source.

4. The tokenizer falls back to a deterministic regex tokenizer if the HuggingFace tokenizer is not cached locally. This keeps chunking token-based and reproducible offline, but it is less model-faithful than the exact embedding tokenizer.

5. Citation validation can remove invalid source IDs and append a retrieved source when a model omits citations, but it cannot prove every generated claim is semantically entailed. Human review or RAGAS-style LLM evaluation is still useful.
