from groq import Groq
from dotenv import load_dotenv
from typing import List, Dict
import os
import re

from ingest.loaders import normalize_source_id

load_dotenv()

REFUSAL = "I cannot find this in the provided documents."

SYSTEM_PROMPT = """You are a helpful assistant that answers questions ONLY based on the provided FastAPI documentation context.

STRICT RULES:
1. Answer ONLY using information explicitly stated in the context below
2. For EVERY factual claim, cite one of the allowed citation IDs in brackets like [source: tutorial/first-steps]
3. Use ONLY these allowed citation IDs: {allowed_citations}
4. If any retrieved context supports the question, answer the supported part with citations
5. If the answer is not found in the context, respond EXACTLY with: "I cannot find this in the provided documents."
6. Never cite a source ID that is not listed in the context
7. Never use your general knowledge to supplement answers
8. Be concise and precise

Required citation format:
[source: citation_id]

Unsupported response:
I cannot find this in the provided documents.

Context:
{context}"""

CITATION_RE = re.compile(r"\[source:\s*([^\]]+?)\s*\]")


def _chunk_citation_id(chunk: Dict) -> str:
    meta = chunk.get("metadata", {})
    return meta.get("citation_id") or meta.get("source_id") or normalize_source_id(meta.get("source", "unknown"))


def _allowed_citations(chunks: List[Dict]) -> List[str]:
    seen = []
    for chunk in chunks:
        cid = _chunk_citation_id(chunk)
        if cid not in seen:
            seen.append(cid)
    return seen


def _extract_citations(answer: str) -> List[str]:
    return [match.strip() for match in CITATION_RE.findall(answer)]


def validate_citations(answer: str, chunks: List[Dict]) -> Dict:
    """Validate and normalize source citations against retrieved chunks."""
    allowed = set(_allowed_citations(chunks))
    cited = _extract_citations(answer)
    invalid = [cid for cid in cited if cid not in allowed]

    for cid in invalid:
        normalized = normalize_source_id(cid)
        if normalized in allowed:
            answer = answer.replace(f"[source: {cid}]", f"[source: {normalized}]")
        else:
            answer = answer.replace(f"[source: {cid}]", "")

    if REFUSAL not in answer and not _extract_citations(answer) and chunks:
        answer = f"{answer.rstrip()} [source: {_chunk_citation_id(chunks[0])}]"

    cited = [cid for cid in _extract_citations(answer) if cid in allowed]
    return {"answer": answer.strip(), "cited_ids": sorted(set(cited)), "invalid_citations": invalid}

def format_context(chunks: List[Dict]) -> str:
    """Format retrieved chunks into context string."""
    parts = []
    for i, chunk in enumerate(chunks):
        source = chunk["metadata"].get("source", "unknown")
        title = chunk["metadata"].get("title", "unknown")
        citation_id = _chunk_citation_id(chunk)
        parts.append(
            f"[citation_id: {citation_id}]\n"
            f"[source: {source}]\n"
            f"[title: {title}]\n"
            f"{chunk['text']}"
        )
    return "\n\n---\n\n".join(parts)

class Generator:
    """LLM generator using Groq API."""
    
    def __init__(self, model: str = "llama-3.1-8b-instant"):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = model
    
    def generate(self, question: str, chunks: List[Dict]) -> Dict:
        """Generate answer from question and chunks."""
        context = format_context(chunks)
        allowed = _allowed_citations(chunks)
        system = SYSTEM_PROMPT.format(context=context, allowed_citations=", ".join(allowed))
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": question}
            ],
            temperature=0.1,  # Low for factual grounding
            max_tokens=1024
        )
        
        answer = response.choices[0].message.content.strip()
        validation = validate_citations(answer, chunks)
        answer = validation["answer"]
        cited_ids = validation["cited_ids"]
        sources = []
        for c in chunks:
            if _chunk_citation_id(c) in cited_ids:
                sources.append(c["metadata"]["source"])
        if not cited_ids and REFUSAL not in answer:
            sources = [chunks[0]["metadata"]["source"]] if chunks else []
        
        return {
            "answer": answer,
            "sources": sorted(set(sources)),
            "cited_ids": cited_ids,
            "retrieved_sources": sorted({c["metadata"]["source"] for c in chunks}),
            "invalid_citations": validation["invalid_citations"],
            "chunks_used": chunks,
            "is_refusal": REFUSAL in answer
        }
