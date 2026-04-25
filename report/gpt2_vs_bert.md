# GPT-2 vs BERT in This RAG System

GPT-2 is a decoder-only Transformer. It uses causal self-attention, so each token can only attend to earlier tokens. Its pretraining objective is autoregressive language modeling: predict the next token. This makes GPT-style models natural generators for the final answer stage of a RAG pipeline. They are optimized to continue text fluently from instructions and retrieved context.

BERT is an encoder-only Transformer. It uses bidirectional self-attention, so each token can attend to both left and right context. Its original pretraining objectives were masked language modeling and next sentence prediction. This bidirectional encoding makes BERT-style models strong for understanding and representation learning.

The embedding model in this project, `sentence-transformers/all-MiniLM-L6-v2`, is a sentence-transformer model built from a BERT-like encoder family. It maps questions and document chunks into comparable dense vectors, which is exactly the retrieval problem: find semantically similar passages.

In short:

- BERT-style encoder: retrieval and semantic matching
- GPT-style decoder: grounded answer generation

RAG combines both roles. The encoder retrieves relevant private/domain-specific evidence, and the decoder turns that evidence into a concise cited answer.
