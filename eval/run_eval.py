from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional

from sentence_transformers import SentenceTransformer, util

sys.path.append(".")

from generation.generator import REFUSAL
from ingest.loaders import normalize_source_id
from pipeline import RAGPipeline
from retrieval.store import COLLECTION_NAME, EMBED_MODEL, VectorStore

# Local evaluator using embeddings
embed_model = SentenceTransformer(EMBED_MODEL)

def compute_similarity(text1: str, text2: str) -> float:
    """Compute cosine similarity between two texts."""
    embeddings = embed_model.encode([text1, text2])
    similarity = util.cos_sim(embeddings[0], embeddings[1])
    return float(similarity)

def evaluate_answer_relevance(question: str, answer: str) -> float:
    """Answer relevance: similarity between question and answer."""
    return compute_similarity(question, answer)

def evaluate_faithfulness(answer: str, context: str) -> float:
    """Faithfulness: similarity between answer and context."""
    return compute_similarity(answer, context)

def evaluate_citation_validity(answer: str, sources: List[str], ground_truth_source: str) -> float:
    """Citation validity: check if correct source is cited."""
    cited_sources = []
    # Extract sources from answer (e.g., [source: tutorial/path-params])
    matches = re.findall(r'\[source:\s*([^\]]+)\]', answer)
    cited_sources = [m.strip() for m in matches]
    
    # Check if ground_truth_source is in cited_sources
    if ground_truth_source in cited_sources:
        return 1.0
    return 0.0

def evaluate_refusal_accuracy(expected_refusal: bool, got_refusal: bool) -> float:
    """Refusal accuracy: 1.0 if match, 0.0 otherwise."""
    return 1.0 if expected_refusal == got_refusal else 0.0


def _terms(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9_-]+", text)}


def _chunk_source_id(chunk: Dict) -> str:
    meta = chunk.get("metadata", {})
    return meta.get("source_id") or meta.get("citation_id") or normalize_source_id(meta.get("source", ""))


def precision_at_k(retrieved_chunks: List[Dict], expected_source_id: str, k: int = 5) -> float:
    if expected_source_id == "none":
        return 0.0
    top = retrieved_chunks[:k]
    if not top:
        return 0.0
    relevant = sum(1 for chunk in top if expected_source_id in _chunk_source_id(chunk))
    return relevant / k


def recall_at_k(retrieved_chunks: List[Dict], expected_source_id: str, k: int = 5) -> float:
    if expected_source_id == "none":
        return 0.0
    return 1.0 if any(expected_source_id in _chunk_source_id(chunk) for chunk in retrieved_chunks[:k]) else 0.0


def answer_relevance_proxy(reference_answer: str, retrieved_chunks: List[Dict]) -> float:
    """Lexical proxy: how much of the reference answer appears in retrieved context."""
    answer_terms = _terms(reference_answer)
    if not answer_terms:
        return 0.0
    context_terms = _terms(" ".join(chunk["text"] for chunk in retrieved_chunks))
    return len(answer_terms & context_terms) / len(answer_terms)


def faithfulness_proxy(answer: str, retrieved_chunks: List[Dict]) -> Optional[float]:
    """Lexical proxy used when RAGAS is unavailable: generated answer terms grounded in context."""
    if not answer or REFUSAL in answer:
        return None
    answer_terms = _terms(re.sub(r"\[source:[^\]]+\]", "", answer))
    if not answer_terms:
        return None
    context_terms = _terms(" ".join(chunk["text"] for chunk in retrieved_chunks))
    return len(answer_terms & context_terms) / len(answer_terms)


def evaluate(args: argparse.Namespace) -> None:
    qa_items = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    store = VectorStore(args.persist_dir, args.collection, args.embedding_model)
    rag = RAGPipeline(top_k=args.top_k, persist_dir=args.persist_dir, collection_name=args.collection) if args.generation else None

    retrieval_results = []
    generation_results = []
    for item in qa_items:
        expected_source_id = item.get("source_id") or normalize_source_id(item.get("source", "none"))
        chunks = store.query(item["question"], top_k=args.top_k)
        p5 = precision_at_k(chunks, expected_source_id, min(5, args.top_k))
        r5 = recall_at_k(chunks, expected_source_id, min(5, args.top_k))
        relevance = answer_relevance_proxy(item.get("reference_answer") or item.get("ground_truth", ""), chunks)

        retrieval_results.append({
            "question": item["question"],
            "expected_source_id": expected_source_id,
            "expected_refusal": item.get("expected_refusal", expected_source_id == "none"),
            "precision_at_5": p5,
            "recall_at_5": r5,
            "answer_relevance_proxy": relevance,
            "retrieved": [
                {
                    "rank": rank + 1,
                    "score": chunk["score"],
                    "source_id": _chunk_source_id(chunk),
                    "citation_id": chunk["metadata"].get("citation_id"),
                    "source": chunk["metadata"].get("source"),
                    "title": chunk["metadata"].get("title"),
                }
                for rank, chunk in enumerate(chunks)
            ],
        })

        if rag is not None:
            result = rag.ask(item["question"])
            context = " ".join([chunk["text"] for chunk in result["chunks_used"]])
            answer_relevance = evaluate_answer_relevance(item["question"], result["answer"])
            faithfulness = evaluate_faithfulness(result["answer"], context)
            citation_validity = evaluate_citation_validity(result["answer"], result["sources"], expected_source_id)
            refusal_acc = evaluate_refusal_accuracy(item.get("expected_refusal", expected_source_id == "none"), result["is_refusal"])
            
            generation_results.append({
                "question": item["question"],
                "answer": result["answer"],
                "is_refusal": result["is_refusal"],
                "expected_refusal": item.get("expected_refusal", expected_source_id == "none"),
                "cited_ids": result.get("cited_ids", []),
                "faithfulness_proxy": faithfulness_proxy(result["answer"], result["chunks_used"]),
                "answer_relevance_similarity": answer_relevance,
                "faithfulness_similarity": faithfulness,
                "citation_validity": citation_validity,
                "refusal_accuracy": refusal_acc,
                "invalid_citations": result.get("invalid_citations", []),
            })

    supported = [r for r in retrieval_results if not r["expected_refusal"]]
    unsupported = [r for r in retrieval_results if r["expected_refusal"]]
    faithfulness_values = [
        r["faithfulness_proxy"] for r in generation_results
        if r.get("faithfulness_proxy") is not None
    ]
    answer_relevance_values = [
        r["answer_relevance_similarity"] for r in generation_results
        if r.get("answer_relevance_similarity") is not None
    ]
    faithfulness_similarity_values = [
        r["faithfulness_similarity"] for r in generation_results
        if r.get("faithfulness_similarity") is not None
    ]
    citation_validity_values = [
        r["citation_validity"] for r in generation_results
        if r.get("citation_validity") is not None
    ]
    refusal_accuracy_values = [
        r["refusal_accuracy"] for r in generation_results
        if r.get("refusal_accuracy") is not None
    ]

    metrics = {
        "dataset_size": len(qa_items),
        "supported_questions": len(supported),
        "unsupported_questions": len(unsupported),
        "top_k": args.top_k,
        "precision_at_5": mean([r["precision_at_5"] for r in supported]) if supported else None,
        "recall_at_5": mean([r["recall_at_5"] for r in supported]) if supported else None,
        "answer_relevance_proxy": mean([r["answer_relevance_proxy"] for r in supported]) if supported else None,
        "generation_enabled": args.generation,
        "faithfulness_proxy": mean(faithfulness_values) if faithfulness_values else None,
        "answer_relevance_similarity": mean(answer_relevance_values) if answer_relevance_values else None,
        "faithfulness_similarity": mean(faithfulness_similarity_values) if faithfulness_similarity_values else None,
        "citation_validity": mean(citation_validity_values) if citation_validity_values else None,
        "refusal_accuracy": None,
        "notes": [],
    }

    if generation_results:
        refusal_cases = [r for r in generation_results if r["expected_refusal"]]
        if refusal_cases:
            metrics["refusal_accuracy"] = mean([r["refusal_accuracy"] for r in refusal_cases if r.get("refusal_accuracy") is not None])
    else:
        metrics["notes"].append("Generation metrics were skipped. Run with --generation to call the LLM API.")

    Path(args.out_dir).mkdir(parents=True, exist_ok=True)
    Path(args.out_dir, "retrieval_results.json").write_text(
        json.dumps(retrieval_results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    Path(args.out_dir, "results.json").write_text(
        json.dumps(retrieval_results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    Path(args.out_dir, "metrics_summary.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    Path(args.out_dir, "ragas_results.json").write_text(
        json.dumps(
            {
                "ragas_run": False,
                "reason": "RAGAS was not invoked by this lightweight evaluator.",
                "equivalent_metrics": {
                    "answer_relevance_proxy": metrics["answer_relevance_proxy"],
                    "faithfulness_proxy": metrics["faithfulness_proxy"],
                    "answer_relevance_similarity": metrics["answer_relevance_similarity"],
                    "faithfulness_similarity": metrics["faithfulness_similarity"],
                    "citation_validity": metrics["citation_validity"],
                    "refusal_accuracy": metrics["refusal_accuracy"],
                },
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    if generation_results:
        Path(args.out_dir, "generation_results.json").write_text(
            json.dumps(generation_results, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    print(json.dumps(metrics, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval and optional generation quality.")
    parser.add_argument("--dataset", default="eval/qa_dataset.json")
    parser.add_argument("--out-dir", default="eval")
    parser.add_argument("--persist-dir", default="data/chroma")
    parser.add_argument("--collection", default=COLLECTION_NAME)
    parser.add_argument("--embedding-model", default=EMBED_MODEL)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--generation", action="store_true", help="Call the LLM API and compute generation proxies.")
    evaluate(parser.parse_args())


if __name__ == "__main__":
    main()
