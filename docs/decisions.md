# MatchIQ Design Decisions

| ID | Date | Decision | Reason |
|---|---|---|---|
| D1 | 2026-10-06 | Primary task is record linkage. Deduplication is a stretch goal. | Focus on MVP value; dedup requires clustering which adds complexity. |
| D2 | 2026-10-06 | Model is trained OFFLINE and applied to user uploads. | Users upload unlabeled data; cannot train on it. Features must be schema-agnostic. |
| D3 | 2026-10-06 | Prevent data leakage in evaluation (split by entity, not pair). | If same record in train and test, metrics are inflated. |
| D4 | 2026-10-06 | Baseline ladder (B0 to tree models). | ML has to earn its place compared to strong rule-based baselines. |
| D5 | 2026-10-06 | Calibrated probabilities. | Tree models don't output true probabilities; needed for thresholding. |
| D6 | 2026-10-06 | Three-way decision with thresholds chosen from data. | Allow human-in-the-loop for uncertain pairs (MATCH/REVIEW/NON-MATCH). |
| D7 | 2026-10-06 | Pair scoring ≠ final linking (resolution modes). | A record might match multiple; need one-to-one resolution. |
| D8 | 2026-10-06 | Async job model from day one (without Celery). | Large inputs exceed HTTP timeouts; Celery is too complex for MVP. |
| D9 | 2026-10-06 | Storage split: PostgreSQL for metadata, Parquet for data. | Matrix sizes too large for DB; keep user data in files. |
| D10| 2026-10-06 | Explainability starts simple (per-field similarity breakdown). | Easy to implement MVP; adds immediate value. |
| D11| 2026-10-06 | Embeddings and pgvector are deferred. | Most value from tabular/string features; embeddings are experimental. |
| D12| 2026-10-06 | Indian-data specifics are a feature. | Public benchmarks are Western; our demo must handle Indian patterns. |
| D13| 2026-10-06 | Default Blocker Set includes Exact Phone/Email, Name Key, Token Match, and TF-IDF kNN. | Union of simple exact match (phone/email), phonetic match, and TF-IDF kNN yields 100% completeness on test datasets (Febrl4 and Synthetic-India) while retaining a high reduction ratio (~97-98%). |
