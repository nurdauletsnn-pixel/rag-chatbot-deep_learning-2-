from retrieval.store import VectorStore
from generation.generator import Generator
from typing import Dict

class RAGPipeline:
    """End-to-end RAG pipeline."""
    
    def __init__(self, top_k: int = 5, persist_dir: str = "data/chroma", collection_name: str = "fastapi_docs"):
        self.store = VectorStore(persist_dir=persist_dir, collection_name=collection_name)
        self.generator = Generator()
        self.top_k = top_k
    
    def ask(self, question: str) -> Dict:
        """Process question through retrieval and generation."""
        chunks = self.store.query(question, top_k=self.top_k)
        result = self.generator.generate(question, chunks)
        return result

if __name__ == "__main__":
    rag = RAGPipeline()
    
    # Test normal query
    r = rag.ask("How do I create a path parameter in FastAPI?")
    print("Answer:", r["answer"])
    print("Sources:", r["sources"])
    
    # Test refusal
    r2 = rag.ask("How do I train a neural network in PyTorch?")
    print("\nRefusal test:", r2["answer"])
