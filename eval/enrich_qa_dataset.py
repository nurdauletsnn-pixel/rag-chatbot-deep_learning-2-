import json
import re
import sys
from pathlib import Path
from typing import Dict, List

sys.path.append(".")

from ingest.loaders import Document, load_all, normalize_source_id


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9_-]+", text)}


def _candidate_passages(doc: Document) -> List[str]:
    passages = [p.strip() for p in re.split(r"\n{2,}", doc.page_content) if len(p.strip()) > 80]
    if not passages:
        passages = [doc.page_content[:800]]
    return passages


def _best_passages(question: str, answer: str, docs: List[Document], source_hint: str, limit: int = 2) -> List[Dict]:
    source_id = normalize_source_id(source_hint)
    candidates = [
        doc for doc in docs
        if source_id in doc.metadata.get("source_id", "") or source_hint in doc.metadata.get("source", "")
    ]
    if not candidates:
        return []

    query_terms = _tokens(f"{question} {answer}")
    scored = []
    for doc in candidates:
        for passage in _candidate_passages(doc):
            score = len(query_terms & _tokens(passage))
            scored.append((score, doc, passage))
    scored.sort(key=lambda item: item[0], reverse=True)

    passages = []
    for _, doc, passage in scored[:limit]:
        passages.append({
            "source_id": doc.metadata["source_id"],
            "citation_id": doc.metadata["citation_id"],
            "source": doc.metadata["source"],
            "title": doc.metadata["title"],
            "text": passage[:1200],
        })
    return passages


def main() -> None:
    qa_path = Path("eval/qa_dataset.json")
    qa_items = json.loads(qa_path.read_text(encoding="utf-8"))
    docs = load_all()

    enriched = []
    for item in qa_items:
        source = item.get("source", "none")
        reference_answer = item.get("reference_answer") or item.get("ground_truth", "")
        if source == "none":
            enriched.append({
                **item,
                "reference_answer": reference_answer,
                "source_id": "none",
                "ground_truth_passages": [],
                "expected_refusal": True,
            })
            continue

        enriched.append({
            **item,
            "reference_answer": reference_answer,
            "source_id": normalize_source_id(source),
            "ground_truth_passages": _best_passages(item["question"], reference_answer, docs, source),
            "expected_refusal": False,
        })

    qa_path.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Enriched {len(enriched)} QA items in {qa_path}")


if __name__ == "__main__":
    main()
