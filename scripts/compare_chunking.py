import json
import sys
from pathlib import Path
from statistics import mean

sys.path.append(".")

from eval.run_eval import precision_at_k, recall_at_k
from ingest.chunkers import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, chunk_documents
from ingest.loaders import load_all, normalize_source_id
from retrieval.store import EMBED_MODEL, VectorStore


def build_and_score(strategy: str, docs, qa_items):
    chunks = chunk_documents(
        docs,
        strategy=strategy,
        chunk_size=DEFAULT_CHUNK_SIZE,
        chunk_overlap=DEFAULT_CHUNK_OVERLAP,
        tokenizer_model=EMBED_MODEL,
    )
    store = VectorStore(f"eval/chunking_{strategy}_index", collection_name="fastapi_docs", reset=True)
    store.index(chunks)

    rows = []
    for item in qa_items:
        if item.get("expected_refusal", item.get("source") == "none"):
            continue
        expected_source_id = item.get("source_id") or normalize_source_id(item["source"])
        retrieved = store.query(item["question"], top_k=5)
        rows.append({
            "question": item["question"],
            "precision_at_5": precision_at_k(retrieved, expected_source_id, 5),
            "recall_at_5": recall_at_k(retrieved, expected_source_id, 5),
        })
    return {
        "strategy": strategy,
        "chunk_count": len(chunks),
        "precision_at_5": mean([row["precision_at_5"] for row in rows]),
        "recall_at_5": mean([row["recall_at_5"] for row in rows]),
        "results": rows,
    }


def main() -> None:
    docs = load_all()
    qa_items = json.loads(Path("eval/qa_dataset.json").read_text(encoding="utf-8"))
    results = [build_and_score(strategy, docs, qa_items) for strategy in ["fixed", "semantic"]]
    Path("eval/chunking_comparison.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    for result in results:
        print(
            f"{result['strategy']}: chunks={result['chunk_count']} "
            f"P@5={result['precision_at_5']:.3f} R@5={result['recall_at_5']:.3f}"
        )
    winner = max(results, key=lambda item: (item["precision_at_5"], item["recall_at_5"]))
    print(f"Winner: {winner['strategy']}")


if __name__ == "__main__":
    main()
