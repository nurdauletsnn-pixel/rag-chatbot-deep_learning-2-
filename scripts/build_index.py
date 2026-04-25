import sys
sys.path.append(".")

import argparse

from ingest.loaders import load_all
from ingest.chunkers import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, chunk_documents
from retrieval.store import COLLECTION_NAME, EMBED_MODEL, VectorStore

def main() -> None:
    """Run full ingestion → chunking → embedding → indexing."""
    parser = argparse.ArgumentParser(description="Build or rebuild the FastAPI RAG vector index.")
    parser.add_argument("--strategy", choices=["fixed", "semantic"], default="semantic")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    parser.add_argument("--persist-dir", default="data/chroma")
    parser.add_argument("--collection", default=COLLECTION_NAME)
    parser.add_argument("--embedding-model", default=EMBED_MODEL)
    parser.add_argument("--no-reset", action="store_true", help="Upsert into the existing collection instead of rebuilding it.")
    args = parser.parse_args()

    print("=== Loading documents ===")
    docs = load_all()
    print(f"Total: {len(docs)} documents")
    
    print(f"\n=== Chunking ({args.strategy}, size={args.chunk_size}, overlap={args.overlap}) ===")
    chunks = chunk_documents(
        docs,
        strategy=args.strategy,
        chunk_size=args.chunk_size,
        chunk_overlap=args.overlap,
        tokenizer_model=args.embedding_model,
    )
    
    print("\n=== Building vector index ===")
    store = VectorStore(
        persist_dir=args.persist_dir,
        collection_name=args.collection,
        embedding_model=args.embedding_model,
        reset=not args.no_reset,
    )
    store.index(chunks)
    
    print("\n✓ Index built successfully!")
    
    # Quick test
    results = store.query("How do I define a path parameter?", top_k=3)
    print("\nTest query results:")
    for r in results:
        print(f"  [{r['score']:.3f}] {r['metadata']['title']}: {r['text'][:100]}...")

if __name__ == "__main__":
    main()
