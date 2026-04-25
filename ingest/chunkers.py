from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Sequence

from langchain_text_splitters import RecursiveCharacterTextSplitter

from ingest.loaders import Document


DEFAULT_TOKENIZER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_CHUNK_SIZE = 256
DEFAULT_CHUNK_OVERLAP = 50
MIN_CHUNK_TOKENS = 100
MAX_CHUNK_TOKENS = 512


@dataclass
class TokenizerAdapter:

    model_name: str = DEFAULT_TOKENIZER_MODEL

    def __post_init__(self) -> None:
        self._tokenizer = None
        try:
            from transformers import AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=True)
            self.backend = f"hf:{self.model_name}"
        except Exception:
            self.backend = "regex"

    def encode(self, text: str) -> List[int] | List[str]:
        if self._tokenizer is not None:
            return self._tokenizer.encode(text, add_special_tokens=False)
        return re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)

    def decode(self, tokens: Sequence[int] | Sequence[str]) -> str:
        if self._tokenizer is not None:
            return self._tokenizer.decode(tokens, skip_special_tokens=True).strip()
        return " ".join(str(t) for t in tokens).strip()

    def count(self, text: str) -> int:
        return len(self.encode(text))


def _validate_chunk_params(chunk_size: int, chunk_overlap: int) -> None:
    if chunk_size < MIN_CHUNK_TOKENS or chunk_size > MAX_CHUNK_TOKENS:
        raise ValueError(f"chunk_size must be between {MIN_CHUNK_TOKENS} and {MAX_CHUNK_TOKENS} tokens")
    min_overlap = int(chunk_size * 0.10)
    max_overlap = int(chunk_size * 0.25)
    if chunk_overlap < min_overlap or chunk_overlap > max_overlap:
        raise ValueError(
            f"chunk_overlap must be 10-25% of chunk_size ({min_overlap}-{max_overlap} tokens for {chunk_size})"
        )


def _merge_small_chunks(splits: List[str], tokenizer: TokenizerAdapter, min_tokens: int = MIN_CHUNK_TOKENS) -> List[str]:
    """Merge tiny trailing/intermediate chunks to satisfy the assignment minimum where possible."""
    merged: List[str] = []
    buffer = ""
    for split in splits:
        candidate = f"{buffer}\n\n{split}".strip() if buffer else split.strip()
        if tokenizer.count(candidate) < min_tokens:
            buffer = candidate
            continue
        merged.append(candidate)
        buffer = ""

    if buffer:
        if merged:
            merged[-1] = f"{merged[-1]}\n\n{buffer}".strip()
        else:
            merged.append(buffer)
    return [chunk for chunk in merged if chunk.strip()]


def _with_chunk_metadata(
    doc: Document,
    split: str,
    index: int,
    strategy: str,
    tokenizer: TokenizerAdapter,
    chunk_size: int,
    chunk_overlap: int,
) -> Document:
    return Document(
        page_content=split,
        metadata={
            **doc.metadata,
            "chunk_index": index,
            "strategy": strategy,
            "chunk_size_tokens": chunk_size,
            "chunk_overlap_tokens": chunk_overlap,
            "token_count": tokenizer.count(split),
        },
    )


def fixed_size_chunks(
    docs: List[Document],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    tokenizer_model: str = DEFAULT_TOKENIZER_MODEL,
) -> List[Document]:
    """Strategy A: fixed-size token windows with overlap."""
    _validate_chunk_params(chunk_size, chunk_overlap)
    tokenizer = TokenizerAdapter(tokenizer_model)
    chunks: List[Document] = []

    for doc in docs:
        tokens = tokenizer.encode(doc.page_content)
        step = chunk_size - chunk_overlap
        raw_splits = [
            tokenizer.decode(tokens[start : start + chunk_size])
            for start in range(0, len(tokens), step)
            if tokens[start : start + chunk_size]
        ]
        splits = _merge_small_chunks(raw_splits, tokenizer)
        for i, split in enumerate(splits):
            chunks.append(_with_chunk_metadata(doc, split, i, "fixed", tokenizer, chunk_size, chunk_overlap))

    print(f"Strategy A (fixed token): {len(chunks)} chunks using {tokenizer.backend}")
    return chunks


def semantic_chunks(
    docs: List[Document],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    tokenizer_model: str = DEFAULT_TOKENIZER_MODEL,
) -> List[Document]:
    """Strategy B: sentence/paragraph-aware recursive splitting measured in tokens."""
    _validate_chunk_params(chunk_size, chunk_overlap)
    tokenizer = TokenizerAdapter(tokenizer_model)
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " "],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=tokenizer.count,
    )
    chunks: List[Document] = []
    for doc in docs:
        splits = _merge_small_chunks(splitter.split_text(doc.page_content), tokenizer)
        for i, split in enumerate(splits):
            chunks.append(_with_chunk_metadata(doc, split, i, "semantic", tokenizer, chunk_size, chunk_overlap))

    print(f"Strategy B (semantic token): {len(chunks)} chunks using {tokenizer.backend}")
    return chunks


def chunk_documents(
    docs: List[Document],
    strategy: str = "semantic",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    tokenizer_model: str = DEFAULT_TOKENIZER_MODEL,
) -> List[Document]:
    if strategy == "fixed":
        return fixed_size_chunks(docs, chunk_size, chunk_overlap, tokenizer_model)
    if strategy == "semantic":
        return semantic_chunks(docs, chunk_size, chunk_overlap, tokenizer_model)
    raise ValueError("strategy must be 'fixed' or 'semantic'")
