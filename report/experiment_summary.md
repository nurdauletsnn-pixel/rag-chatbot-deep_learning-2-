# Experiment Summary

All experiments were run on the full evaluation dataset using retrieval metrics. Chunking experiments rebuild a fresh Chroma index before scoring.

| Component changed | Before | After | Metric before | Metric after | Observation |
|---|---|---|---:|---:|---|
| chunking_strategy | semantic | fixed | 0.5467 | 0.5733 | Fixed chunks improved P@5 and R@5. |
| chunk_size | 256 tokens | 384 tokens | 0.5467 | 0.4933 | Larger chunks reduced precision. |
| chunk_size | 256 tokens | 200 tokens | 0.5467 | 0.5667 | Smaller chunks improved precision slightly. |
| overlap | 50 tokens (~20%) | 26 tokens (~10%) | 0.5467 | 0.5133 | Lower overlap reduced precision. |
| top_k | 5 | 3 | 0.5467 | 0.5778 | Precision improved, but recall dropped from 0.867 to 0.800. |
| top_k | 5 | 10 | 0.5467 | 0.5467 | No precision gain over top_k=5 in this metric. |

The final production index uses fixed token chunking with `chunk_size=256`, `overlap=50`, and UI default `top_k=5`. Although top_k=3 had a higher precision denominator effect, top_k=5 preserved stronger recall for demo reliability.
