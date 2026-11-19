# Phase 5 local latency evaluation

Detection timing used 3 warmed passes over 18 synthetic cases per configuration. spaCy model startup and Gemini/network time are excluded.

| Component | Mean ms/case | Median ms/case | P95 ms/case | Samples |
|---|---:|---:|---:|---:|
| Regex only | 0.0653 | 0.0507 | 0.1271 | 54 |
| NER only | 4.6450 | 4.3800 | 6.5113 | 54 |
| Regex + NER | 4.3484 | 3.9978 | 6.7871 | 54 |
| Chroma retrieval | 14.9721 | 14.5801 | 18.9351 | 24 |

These local measurements are environment- and cache-dependent. They exclude app startup, PDF parsing, embedding-model initialization, and remote Gemini latency.
