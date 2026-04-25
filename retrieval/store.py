from __future__ import annotations

import chromadb
from sentence_transformers import SentenceTransformer
from typing import Any, Dict, List
from ingest.loaders import Document
from tqdm import tqdm

EMBED_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "fastapi_docs"

class VectorStore:
    """Vector store using SentenceTransformer and ChromaDB."""
    
    def __init__(
        self,
        persist_dir: str = "data/chroma",
        collection_name: str = COLLECTION_NAME,
        embedding_model: str = EMBED_MODEL,
        reset: bool = False,
    ):
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.model = self._load_model(embedding_model)
        self.client = chromadb.PersistentClient(path=persist_dir)
        if reset and collection_name in [c.name for c in self.client.list_collections()]:
            self.client.delete_collection(collection_name)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    @staticmethod
    def _load_model(model_name: str) -> SentenceTransformer:
        try:
            return SentenceTransformer(model_name, local_files_only=True)
        except Exception:
            pass
        try:
            return SentenceTransformer(model_name)
        except Exception as exc:
            raise RuntimeError(
                "Could not load the embedding model. Ensure internet is available for the first run "
                f"or pre-download/cache '{model_name}' before building the index."
            ) from exc

    @staticmethod
    def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Keep Chroma metadata values scalar and explicit."""
        clean: Dict[str, Any] = {}
        for key, value in metadata.items():
            if value is None:
                clean[key] = "None"
            elif isinstance(value, (str, int, float, bool)):
                clean[key] = value
            else:
                clean[key] = str(value)
        return clean
    
    def index(self, chunks: List[Document], batch_size: int = 64) -> None:
        """Encode and index all chunks."""
        texts = [c.page_content for c in chunks]
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        metadatas = [self._sanitize_metadata(c.metadata) for c in chunks]
        
        print(f"Encoding {len(texts)} chunks...")
        embeddings = []
        for i in tqdm(range(0, len(texts), batch_size)):
            batch = texts[i:i+batch_size]
            embs = self.model.encode(batch, show_progress_bar=False).tolist()
            embeddings.extend(embs)
        
        # Upsert in batches
        for i in range(0, len(texts), batch_size):
            self.collection.upsert(
                ids=ids[i:i+batch_size],
                embeddings=embeddings[i:i+batch_size],
                documents=texts[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size]
            )
        print(f"Indexed {len(texts)} chunks into ChromaDB ✓")
    
    def query(self, question: str, top_k: int = 5) -> List[Dict]:
        """Retrieve top-k relevant chunks."""
        embedding = self.model.encode([question]).tolist()
        results = self.collection.query(
            query_embeddings=embedding,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            chunks.append({
                "text": doc,
                "metadata": meta,
                "score": 1 - dist  # Cosine similarity
            })
        return chunks
