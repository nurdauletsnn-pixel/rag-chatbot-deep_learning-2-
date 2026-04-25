from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path
from statistics import mean
from typing import Dict, List

sys.path.append(".")

from eval.run_eval import precision_at_k, recall_at_k
from ingest.chunkers import chunk_documents
from ingest.loaders import load_all, normalize_source_id
from retrieval.store import EMBED_MODEL, VectorStore


BASELINE = {
    "strategy": "semantic",
    "chunk_size": 256,
    "overlap": 50,
    "top_k": 5,
}


EXPERIMENTS = [
    {
        "name": "fixed_chunking",
        "component_changed": "chunking_strategy",
        "parameter_before": "semantic",
        "parameter_after": "fixed",
        "config": {**BASELINE, "strategy": "fixed"},
        "requires_rebuild": True,
    },
    {
        "name": "larger_chunks_384",
        "component_changed": "chunk_size",
        "parameter_before": "256 tokens",
        "parameter_after": "384 tokens",
        "config": {**BASELINE, "chunk_size": 384},
        "requires_rebuild": True,
    },
    {
        "name": "smaller_chunks_200",
        "component_changed": "chunk_size",
        "parameter_before": "256 tokens",
        "parameter_after": "200 tokens",
        "config": {**BASELINE, "chunk_size": 200},
        "requires_rebuild": True,
    },
    {
        "name": "lower_overlap_10pct",
        "component_changed": "overlap",
        "parameter_before": "50 tokens (~20%)",
        "parameter_after": "26 tokens (~10%)",
        "config": {**BASELINE, "overlap": 26},
        "requires_rebuild": True,
    },
    {
        "name": "top_k_3",
        "component_changed": "top_k",
        "parameter_before": "5",
        "parameter_after": "3",
        "config": {**BASELINE, "top_k": 3},
        "requires_rebuild": False,
    },
    {
        "name": "top_k_10",
        "component_changed": "top_k",
        "parameter_before": "5",
        "parameter_after": "10",
        "config": {**BASELINE, "top_k": 10},
        "requires_rebuild": False,
    },
]


def _build_store(name: str, config: Dict, docs: List) -> VectorStore:
    persist_dir = Path("eval/experiment_indexes") / name
    if persist_dir.exists():
        shutil.rmtree(persist_dir)
    chunks = chunk_documents(
        docs,
        strategy=config["strategy"],
        chunk_size=config["chunk_size"],
        chunk_overlap=config["overlap"],
        tokenizer_model=EMBED_MODEL,
    )
    store = VectorStore(str(persist_dir), collection_name="fastapi_docs", reset=True)
    store.index(chunks)
    return store


def _score(store: VectorStore, qa_items: List[Dict], top_k: int) -> Dict:
    rows = []
    for item in qa_items:
        expected_refusal = item.get("expected_refusal", item.get("source") == "none")
        if expected_refusal:
            continue
        expected_source_id = item.get("source_id") or normalize_source_id(item["source"])
        chunks = store.query(item["question"], top_k=top_k)
        rows.append({
            "precision_at_5": precision_at_k(chunks, expected_source_id, min(5, top_k)),
            "recall_at_5": recall_at_k(chunks, expected_source_id, min(5, top_k)),
        })
    return {
        "precision_at_5": mean([row["precision_at_5"] for row in rows]) if rows else 0.0,
        "recall_at_5": mean([row["recall_at_5"] for row in rows]) if rows else 0.0,
    }


def main() -> None:
    docs = load_all()
    qa_items = json.loads(Path("eval/qa_dataset.json").read_text(encoding="utf-8"))
    Path("eval/experiment_indexes").mkdir(parents=True, exist_ok=True)

    baseline_store = _build_store("baseline", BASELINE, docs)
    baseline_score = _score(baseline_store, qa_items, BASELINE["top_k"])

    rows = []
    detailed = {"baseline": {**BASELINE, **baseline_score}, "experiments": []}
    for experiment in EXPERIMENTS:
        config = experiment["config"]
        store = baseline_store if not experiment["requires_rebuild"] else _build_store(experiment["name"], config, docs)
        score = _score(store, qa_items, config["top_k"])
        observation = (
            f"P@5 {baseline_score['precision_at_5']:.3f} -> {score['precision_at_5']:.3f}; "
            f"R@5 {baseline_score['recall_at_5']:.3f} -> {score['recall_at_5']:.3f}"
        )
        row = {
            "component_changed": experiment["component_changed"],
            "parameter_before": experiment["parameter_before"],
            "parameter_after": experiment["parameter_after"],
            "metric_before": round(baseline_score["precision_at_5"], 4),
            "metric_after": round(score["precision_at_5"], 4),
            "observation": observation,
        }
        rows.append(row)
        detailed["experiments"].append({**experiment, "score": score, "observation": observation})

    out_csv = Path("eval/experiment_log.csv")
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "component_changed",
                "parameter_before",
                "parameter_after",
                "metric_before",
                "metric_after",
                "observation",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    Path("eval/experiment_details.json").write_text(json.dumps(detailed, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} experiments to {out_csv}")


if __name__ == "__main__":
    main()
