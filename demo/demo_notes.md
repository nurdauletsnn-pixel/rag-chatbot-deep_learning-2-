# Demo Notes

## Known Good In-Domain Queries

1. What is Depends() used for?
   - Expected citation: `tutorial/dependencies`
   - Retrieval quality in eval: P@5 1.0, R@5 1.0

2. How do I handle file uploads?
   - Expected citation: `tutorial/request-files`
   - Retrieval quality in eval: P@5 1.0, R@5 1.0

3. How do I use WebSockets?
   - Expected citation: `advanced/websockets`
   - Retrieval quality in eval: P@5 1.0, R@5 1.0

## Refusal Query

How do I train a neural network in PyTorch?

Expected behavior:

`I cannot find this in the provided documents.`

## Design Decision to Explain

The project originally used semantic recursive chunking. After evaluating both strategies on the full QA dataset, fixed token chunks performed better:

- Fixed token: P@5 0.573, R@5 0.900
- Semantic token: P@5 0.547, R@5 0.867

The production index was rebuilt with fixed token chunking as a result.
