# CineMente — Evaluation Suite

> Part of the CineMente Final Degree Project · Universitat de Girona · June 2026  
> Author: **Guillem Salguero Montes**

Evaluation toolkit for the CineMente RAG-based movie recommendation system. Contains three complementary metrics to assess retrieval quality across five retrieval modules: Hybrid, Self-Querying, Multi-Query, Parent Retrieval, and Combined.

---

## Table of Contents

- [Metrics](#metrics)
- [Files](#files)
- [Getting started](#getting-started)
- [Results summary](#results-summary)
- [Related repositories](#related-repositories)

---

## Metrics

All five retrieval modules are evaluated against the same set of 12 reference queries, organised in four categories: abstract/emotional, explicit metadata, niche, and contradictory.

### LLM-as-a-Judge
Uses `Llama-3.3-70B` as an automated evaluator. For each query, the model receives the top-10 results (title, year, genre, Tomatometer) and scores 0–100 how well the list satisfies the original query intent. Implemented in `dashboard_eval.py`.

### Algorithm Retrieval (Catalog Coverage)
Counts the number of unique titles recovered by each module across all queries — a proxy for corpus recall. Maximum theoretical coverage: 120 unique titles (12 queries × 10 results, no overlap). Implemented in `CatalogCoverage.py`.

### Intra-List Diversity (ILD)
Measures how diverse the results within a single list are. Computed as the average pairwise distance between all movies in a result set, combining:
- **Genre** (50%) — Jaccard distance over label sets
- **Director** (30%) — Jaccard distance over label sets  
- **Release year** (20%) — normalised over a 40-year window

Score ranges from 0 (all results identical) to 1 (maximum diversity). Implemented in `Intra-ListDiversity.py`.

---

## Files

| File | Description |
|------|-------------|
| `dashboard_eval.py` | Streamlit dashboard — runs all three metrics and displays interactive charts |
| `CatalogCoverage.py` | Standalone script for Algorithm Retrieval metric |
| `Intra-ListDiversity.py` | Standalone script for ILD metric |

---

## Getting started

### Prerequisites

- Python 3.10+
- The CineMente AI engine running at `http://localhost:8001` (see [Recomenador repo](https://github.com/GuillemSalguero/Recomenador))
- A `.env` file with `GROQ_API_KEY`

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the full evaluation dashboard

```bash
streamlit run dashboard_eval.py
```

### Run individual metrics

```bash
python CatalogCoverage.py
python Intra-ListDiversity.py
```

---

## Results summary

| Module | Unique titles | ILD avg | Best at |
|--------|:---:|:---:|---|
| Self-Query | 89 | 0.17 | Explicit metadata filters |
| Hybrid | 117 | 0.73 | Precision / coverage balance |
| Multi-Query | 68 | 0.76 | Abstract / emotional queries |
| Combined | 94 | 0.76 | Mixed constraint + tone queries |
| Parent | 120 | 0.68 | Maximum corpus coverage |

Key findings:
- **Self-Querying** and **Hybrid** score highest on queries with explicit filters (director, year, score).
- **Combined** and **Multi-Query** perform best on abstract or emotional queries.
- **Parent Retrieval** achieves the broadest corpus coverage thanks to its review aggregation strategy.
- A low ILD is expected (and correct) on constrained queries — it means the system respected the filters.

---

## Related repositories

| Service | Repository |
|---------|-----------|
| AI engine (FastAPI) | [Recomenador](https://github.com/GuillemSalguero/Recomenador) |
| Frontend (React) | [add link] |
| User backend (Spring Boot) | [add link] |

---

*Academic project — Universitat de Girona, June 2026.*
