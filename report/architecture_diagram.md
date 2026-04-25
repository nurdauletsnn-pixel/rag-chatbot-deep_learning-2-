# Architecture Diagram

```mermaid
flowchart LR
    A[FastAPI HTML docs] --> C[Ingestion]
    B[Derived Markdown docs] --> C
    C --> D[Metadata normalization<br/>source, source_id, citation_id, title, date]
    D --> E[Token-aware chunking<br/>fixed or semantic]
    E --> F[SentenceTransformer embeddings<br/>all-MiniLM-L6-v2]
    F --> G[Chroma vector store<br/>text + metadata + chunk_index]
    H[User question] --> I[Dense retrieval top-k]
    G --> I
    I --> J[Grounded context builder<br/>allowed citation IDs]
    J --> K[Groq LLM generation]
    K --> L[Citation validation]
    L --> M[Streamlit answer<br/>citations + evidence panel]
```

The production configuration uses fixed token chunks with `chunk_size=256` and `overlap=50` because this setting had the best measured retrieval result in the current evaluation.
