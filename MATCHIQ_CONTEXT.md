# MatchIQ — Project Context (v2)

> Audience: the AI coding agent (Antigravity) and the human team.
> Status: planning is DONE in this file. Do not re-plan from scratch. Start at **Milestone 0** (Section 13) after the team approves the plan.
> Items marked **[DECIDE]** are open questions with a recommended default. Use the default unless the team says otherwise.

---

## 0. Agent Operating Rules (read first, follow always)

1. **Plan first, code second.** For every task: restate it in 2–3 lines, list the files you will create/modify, then implement. Never build more than the current task.
2. **One task at a time.** Tasks are listed in Section 13 with acceptance criteria. Do not jump ahead to later milestones.
3. **Keep ML separate from the web app.** Everything under `core/` must work without FastAPI, a database, or a browser. The backend imports `core`; `core` never imports the backend.
4. **Simple before clever.** Baseline → logistic regression → tree models → embeddings. No new library or service without a written reason in `docs/decisions.md`.
5. **Never fabricate numbers.** Metrics, speedups, and scale claims must come from a results file in `experiments/results/`. If you have not run it, write `TBD`. This applies to README text, code comments, and resume bullets.
6. **Tests are part of the task.** Normalizers, blockers, feature functions, and metrics need pytest tests (table-driven where possible).
7. **Explain as you go.** After each task, give: what was built, where it fits in the pipeline, key decision(s), how to run/test it. The team must be able to explain every line in an interview.
8. **Keep changes focused.** Do not touch unrelated files. Do not rewrite working code to "improve" it unless asked.
9. **Reproducibility.** Fixed random seeds, config-driven runs (YAML/pydantic), pinned dependencies, no hard-coded paths.
10. **Privacy.** Never send dataset contents to external APIs. Embeddings run locally. Never commit real personal data or secrets (`data/` and `.env` are gitignored).
11. If this file is ambiguous or contradicts itself, **ask** instead of guessing.

---

## 1. What We Are Building

MatchIQ is a web platform for **entity resolution (record linkage)**: given two tabular datasets, decide which records refer to the same real-world entity despite typos, abbreviations, missing fields, and formatting differences, and attach a calibrated confidence and an explanation to each decision.

Example:

| Dataset A | Dataset B | Expected |
|---|---|---|
| Rahul Kumar, Bangalore, 9876543210 | R. Kumar, Bengaluru, +91 98765 43210 | MATCH |
| Rahul Kumar, Bangalore, 9876543210 | Ravi Kumar, Bangalore, *(missing)* | NON-MATCH (hard negative) |
| Priya Nair, 12 MG Rd, Kochi | Priya Nair, 12 M.G. Road, Cochin | MATCH even with no phone/email |

The second and third rows matter. A system that only works when the phone number matches is a phone-number lookup, not an ML project. Test data and experiments must include cases where strong identifiers are missing or wrong.

**Why this project (resume angle):** real ML + real data engineering + real evaluation, not an LLM wrapper. Techniques: blocking, feature engineering, imbalanced classification, probability calibration, threshold tuning, human-in-the-loop review, and a full-stack product around it.

**Not building (initially):** auth, payments, admin panels, mobile app, microservices, Kubernetes, multiple databases, chatbots/agents, real-time collaboration, RBAC.

---

## 2. Key Design Decisions (already made — these fix gaps in the original brief)

### D1. Primary task is record linkage (A ↔ B). Deduplication (A ↔ A) is a stretch goal
Same engine; dedup just compares a dataset to itself with `i < j` and adds clustering (connected components). Do not build dedup in the MVP, but do not make design choices that prevent it.

### D2. The model is trained OFFLINE and applied to user uploads
Users upload unlabeled data, so we cannot train on it. Therefore:
- Features are **schema-agnostic**, computed per *canonical field type* (name, address, phone, email, city, postcode, dob, company, other_text), never per raw column name.
- The training set comes from labeled benchmark/synthetic data. The user's column mapping translates their columns into canonical fields at inference time.
- **Missing ≠ mismatch.** If either side's field is missing, the similarity feature is `NaN` and a `<field>_missing` flag is set. Use models that handle `NaN` natively (LightGBM/XGBoost/`HistGradientBoostingClassifier`) or impute explicitly for Logistic Regression.
- **Field dropout augmentation:** during training, randomly mask fields so the model cannot collapse into "phone equal → match". Verify with an ablation (Experiment E3).
- The dashboard for a user upload shows **estimated** quality (model confidence, review rate), not true accuracy, because there is no ground truth. Optional: let the user upload a ground-truth pairs file to get real metrics. Review labels give a small-sample estimate.

### D3. Prevent data leakage in evaluation
- **Split by entity/cluster, not by pair.** If the same record appears in train and test pairs, metrics are inflated.
- Train on **candidate pairs produced by blocking** (same distribution as inference), with hard negatives included. Use class weights; avoid synthetic oversampling of pairs.
- Report **end-to-end** metrics (blocking + model), not only model-on-pairs. End-to-end recall ≤ blocking recall.
- Tune thresholds on a **validation** set; touch the **test** set once for final numbers.

### D4. Baseline ladder (so ML has to earn its place)
- B0: exact match on a normalized key (e.g., phone or email).
- B1: single-field fuzzy match with a threshold (e.g., name Jaro-Winkler ≥ t).
- B2: weighted average of field similarities with tuned weights + threshold (a strong rule-based baseline).
- Then: Logistic Regression → Random Forest → gradient boosting (LightGBM or XGBoost; choose via E1).
- If ML ≈ B2 on some dataset, report that honestly.
- Optional classical reference: Fellegi–Sunter via Splink.

### D5. Calibrated probabilities
Tree-model scores are not probabilities by default. Calibrate on the validation set (isotonic or Platt), report Brier score and a reliability curve. Only then call the output "confidence".

### D6. Three-way decision with thresholds chosen from data
- `p >= T_high` → MATCH, `p <= T_low` → NON-MATCH, else NEEDS REVIEW.
- Choose `T_high` for a target precision of auto-matches (e.g., ≥ 0.98) and `T_low` for a target recall retention. The 0.60 / 0.85 values in earlier drafts are placeholders only.
- Key trade-off metric: **fraction of pairs sent to review** vs. **precision/recall of the auto-decided pairs**.

### D7. Pair scoring ≠ final linking
After scoring, a record in A may match several records in B. Provide a resolution mode:
- `one_to_one` (default for linkage): greedy by score or Hungarian (`scipy.optimize.linear_sum_assignment`) over predicted matches.
- `one_to_many`: keep all pairs above `T_high` (show top-k per record).
- Dedup (stretch): connected components over match edges.

### D8. Async job model from day one (without Celery)
Even moderately large inputs exceed an HTTP request timeout. The API is job-based from the start: `POST /jobs` returns immediately; processing runs in FastAPI `BackgroundTasks` (or a thread/process pool); the frontend polls `GET /jobs/{id}`. **Do not add Redis/Celery** until a measured need exists (Milestone 8).

### D9. Storage split
- **PostgreSQL:** metadata and things users query/edit — datasets, column mappings, jobs, scored pairs above a floor (e.g., `p >= 0.2`), review labels, model versions.
- **Parquet files on disk (`data/workspace/<job_id>/`):** uploaded data, normalized data, candidate pairs, feature matrices (can be millions of rows; do not put these in Postgres).
- Use SQLAlchemy 2.x + Alembic migrations.

### D10. Explainability starts simple
MVP: show the per-field similarity breakdown for each pair (the feature values themselves). Later: logistic-regression coefficient contributions and SHAP for tree models.

### D11. Embeddings and pgvector are deferred
Names/addresses are mostly handled by character-level and token-level similarity. Embeddings are an **experiment** (E8), not an assumption. If used: local `sentence-transformers` model, in-memory nearest-neighbor search first. Do not add pgvector or a vector DB without evidence.

### D12. Indian-data specifics are a feature, not an afterthought
Many public benchmarks are Western/English. Our synthetic generator and normalizers must handle Indian patterns (Section 7 and 6). This is also what makes the demo feel real.

---

## 3. Pipeline

```
Upload A, B (CSV)
   ↓ validate (encoding, delimiter, size, empty/dup headers)
Profile (rows, cols, dtypes, missing %, samples)
   ↓
Column mapping  (canonical field ← one or more columns per side)
   ↓
Normalize       (pure functions; raw columns kept, normalized added)
   ↓
Blocking        (union of several blockers → candidate pairs)
   ↓
Features        (per canonical field; NaN when missing; missing flags)
   ↓
Model           (load versioned artifact → calibrated probability)
   ↓
Thresholds      (MATCH / REVIEW / NON-MATCH)
   ↓
Resolution      (one-to-one / one-to-many)
   ↓
Review queue    (human labels stored)
   ↓
Analytics + Export
```

Each stage is a function in `core/` with explicit inputs/outputs (DataFrames / Parquet paths + a config object) and is independently testable and runnable from the CLI.

### Column mapping format
```json
{
  "name":    {"a": ["full_name"],               "b": ["customer_name"]},
  "city":    {"a": ["city"],                    "b": ["town"]},
  "phone":   {"a": ["mobile"],                  "b": ["contact_no"]},
  "address": {"a": ["addr_line1", "addr_line2"], "b": ["address"]}
}
```
Multiple source columns are concatenated with a space (needed for e.g. `given_name` + `surname`). Unmapped fields are simply absent (all-NaN features).

---

## 4. Repository Structure

```
matchiq/
├── MATCHIQ_CONTEXT.md          # this file (or AGENTS.md)
├── README.md
├── docker-compose.yml          # postgres for local dev
├── core/                       # pure Python library — NO fastapi/db imports
│   ├── pyproject.toml
│   ├── matchiq/
│   │   ├── io/                 # csv loading, encoding detection, profiling
│   │   ├── normalize/          # one module per field type
│   │   │   └── resources/      # *.yaml: city aliases, address abbreviations, titles, company suffixes
│   │   ├── blocking/           # one blocker per file + union + metrics
│   │   ├── features/           # similarity functions + feature builder
│   │   ├── models/             # train, calibrate, predict, registry, model card
│   │   ├── evaluation/         # precision/recall/F1, blocking metrics, threshold sweep
│   │   ├── synthetic/          # Faker en_IN generator + noise operators
│   │   ├── resolution.py       # one-to-one / one-to-many
│   │   ├── pipeline.py         # orchestrates the stages from a config
│   │   └── cli.py              # e.g. `python -m matchiq.cli baseline --dataset febrl4`
│   └── tests/
├── backend/
│   ├── pyproject.toml          # depends on ../core
│   ├── app/
│   │   ├── main.py
│   │   ├── api/                # routers: datasets, jobs, results, reviews, exports
│   │   ├── schemas/            # pydantic request/response models
│   │   ├── services/           # glue between API and core
│   │   ├── db/                 # SQLAlchemy models, session, alembic/
│   │   └── workers/            # background job runner
│   └── tests/
├── frontend/
│   └── src/ (components, pages, services, hooks, layouts, utils)
├── experiments/
│   ├── configs/                # one YAML per experiment
│   ├── notebooks/              # exploration only; real runs are scripts
│   ├── run_e01_baselines.py ...
│   └── results/                # committed CSVs/PNGs that docs and README cite
├── artifacts/                  # trained model files + model_card.json
├── data/                       # GITIGNORED: raw/, interim/, workspace/
└── docs/                       # decisions.md, architecture.md, ml-methodology.md, experiments.md
```

Do not create folders before they are needed. `core/` and `experiments/` come first; `backend/` and `frontend/` come later.

---

## 5. Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.11+ | ML ecosystem |
| Env/deps | `uv` (or pip + pinned requirements) **[DECIDE]** | reproducible |
| Data | pandas + pyarrow (Parquet) | team familiarity; Polars only if profiling shows a need |
| String sim | `rapidfuzz` | fast Levenshtein / Jaro-Winkler / token ratios, `process.cdist` |
| Phonetics | `jellyfish` (Metaphone etc.) | blocking + phonetic feature |
| Phone | `phonenumbers` | proper parsing, default region IN |
| ML | scikit-learn, LightGBM or XGBoost | compare in E1, keep behind a common interface |
| Synthetic data | `Faker` (`en_IN`) | controlled ground truth |
| Backend | FastAPI, pydantic v2, SQLAlchemy 2, Alembic | |
| DB | PostgreSQL (Docker locally; Supabase optional at deploy) | |
| Frontend | React + Vite + Tailwind; React Router; TanStack Query; Recharts; Axios | add others only when needed |
| Quality | pytest, ruff, (mypy optional) | |
| Later | sentence-transformers, SHAP | Milestone 8 |
| Not now | Redis, Celery, pgvector, vector DB, Kubernetes | see D8, D11 |

---

## 6. Data Strategy

Keep three categories clearly separated in code, docs, and reported results: **public benchmark**, **synthetic**, **manually labeled**.

### Tier 1 — Development datasets (person-like records with ground truth)
1. **Febrl** (Freely Extensible Biomedical Record Linkage), loaded via the `recordlinkage` package (`load_febrl4()` gives two 5,000-record datasets with 5,000 true links; `load_febrl1/2/3` are dedup sets). Fields include given name, surname, address, suburb, postcode, state, date of birth. Synthetic and relatively easy (Australian). **Use this for Milestone 1** because it gives ground truth and a known-good reference immediately.
2. **MatchIQ synthetic-India generator** (we build it, Milestone 2). Faker `en_IN` base entities → dataset A (light noise) and dataset B (heavier noise) with configurable overlap, noise level, and seed. Outputs `A.csv`, `B.csv`, `truth.csv`. Must include:
   - Noise operators: typo (insert/delete/swap/substitute), initials (`Rahul Kumar` → `R. Kumar`), name order swap, titles (Mr/Dr/Shri), common spelling variants, city aliases (Bangalore/Bengaluru, Bombay/Mumbai, Madras/Chennai, Calcutta/Kolkata, Gurgaon/Gurugram, Cochin/Kochi), phone formatting (`+91`, spaces, leading 0), phone digit typo, email domain change/typo, address abbreviation and reordering, missing fields, case/punctuation changes.
   - **Hard negatives:** same surname + same city, family members sharing an address/phone, `R. Kumar` vs several different Rahul/Ravi/Rohit Kumar.
   - This dataset powers the noise-robustness and scalability experiments (can be scaled to 10k–1M+ rows).

### Tier 2 — Generalization datasets (not person-like)
Magellan / DeepMatcher benchmark datasets: Fodors-Zagats (restaurants), DBLP-ACM and DBLP-Scholar (bibliographic), and the harder, text-heavy Abt-Buy and Amazon-Google (products). Use them to test whether the pipeline generalizes. On the product datasets, tabular string features will probably be weak; report that honestly rather than forcing them into the MVP. Verify current download locations and licenses when downloading.

### Tier 3 — Optional
- Splink example datasets (e.g., `fake_1000`) for quick smoke tests.
- North Carolina voter data for a large real-world scale test. Only if the team is comfortable with the privacy/licensing implications. The synthetic generator already covers scale.

### Rules
- `scripts/download_data.py` fetches public datasets into `data/raw/`. Raw data is never committed.
- Every result file records: dataset name, split seed, code commit hash, config.

---

## 7. Normalization Spec

Pure functions `str | None → str | None`, one module per field type, table-driven tests. Raw columns are preserved; normalized values go in separate columns. No LLMs here.

**Global:** Unicode NFKD + strip accents, casefold, collapse whitespace, strip punctuation (keep meaningful chars per field), treat placeholders (`""`, `na`, `n/a`, `null`, `none`, `-`, `unknown`, `0000000000`) as missing.

| Field | Rules |
|---|---|
| name | remove titles (mr, mrs, ms, dr, shri, smt, sri…), remove punctuation in initials (`R.` → `r`), keep token order for display and add a sorted-token form for comparison; optional alias table for common variants (Mohammed/Mohd/Muhammad) |
| phone | parse with `phonenumbers`, default region IN; output canonical national 10-digit form (and E.164); invalid numbers → missing, but keep a `phone_invalid` flag |
| email | lowercase, trim; split local/domain; optional Gmail dot/plus-tag handling behind a config flag |
| address | lowercase, expand/standardize abbreviations from `resources/address_abbrev.yaml` (rd→road, st→street, nr→near, opp→opposite, apt→apartment, blr→bangalore…), normalize `no.`/`#`, extract house/door number and pincode as separate tokens |
| city/state | alias → canonical via `resources/city_aliases.yaml` |
| postcode (PIN) | digits only, 6 digits; else missing |
| company | remove legal suffixes (pvt, private, ltd, limited, llp, inc, corp…), drop "&"/"and" differences |
| dob/date | parse multiple formats to ISO; ambiguous dd/mm vs mm/dd must be configurable |

Alias/abbreviation lists live in YAML so the team can extend them without code changes.

---

## 8. Blocking Spec

Goal: avoid N×M comparisons while keeping almost all true matches. Use a **union of several blockers**, each simple:

1. Exact normalized phone (if mapped).
2. Exact normalized email, plus domain+local-prefix variant.
3. Name key: phonetic code (Metaphone) of last token + first initial (+ city when available).
4. Token blocking on name/address tokens with a **max block size cap** (drop overly common tokens like "kumar", "road").
5. Character 3-gram TF-IDF top-k nearest neighbors (sparse cosine, computed in chunks). Strong generic blocker for typos.

Metrics (computed whenever ground truth exists):
- **Pairs completeness (candidate recall)** = true matches in candidates / total true matches. Primary metric; target ≥ 0.95 on benchmarks (a target, not a claim).
- **Reduction ratio** = 1 − |candidates| / (N × M).
- Pairs quality = true matches in candidates / |candidates|.
- Runtime, and per-blocker marginal contribution.

Choose the final blocker set from measurements on Febrl and the synthetic data, not by intuition.

---

## 9. Feature Spec

One feature vector per candidate pair. Features are computed per canonical field. If either side is missing → `NaN` + missing flag.

| Field | Features |
|---|---|
| name | Jaro-Winkler, normalized Levenshtein, token_sort_ratio, token_set_ratio, token Jaccard, char-3gram Jaccard/cosine, exact-equal, **initial-compatible** (`r kumar` ~ `rahul kumar`), phonetic-equal, length difference |
| address | token_set_ratio, token Jaccard, char-ngram cosine, house-number equal, pincode equal |
| phone | exact (national 10 digits), edit distance ≤ 1, last-7-digits equal |
| email | exact, local-part Jaro-Winkler, domain equal |
| city / state | exact (post-alias), Jaro-Winkler |
| postcode | exact, first-3-digits equal |
| dob | exact, year equal, day/month swapped |
| company | token_set_ratio after suffix removal, Jaro-Winkler |
| other_text | token Jaccard, char-ngram cosine |
| per field | `<field>_missing` flag |

Stretch features: IDF-weighted token overlap (matching on a rare surname is stronger evidence than matching on "Kumar"), embedding cosine (E8).

Feature list and order are stored with the model artifact; prediction must fail loudly if they differ.

---

## 10. Modeling & Evaluation Protocol

- **Labels:** 1 = match, 0 = non-match. Severe class imbalance is expected. Accuracy is NOT a reported metric.
- **Primary metrics:** precision, recall, F1 on the match class; PR-AUC; confusion matrix. ROC-AUC only as a secondary metric (it is misleading under heavy imbalance).
- **Splits:** by entity/cluster (D3). Fixed seeds. Use k-fold or repeated splits for the final comparison and report mean ± std.
- **Calibration:** isotonic/Platt on validation; Brier score; reliability curve.
- **Thresholds:** swept on validation; chosen per D6; final numbers on test.
- **Model artifact:** `artifacts/<model_id>/model.joblib` + `model_card.json` (feature list, training datasets, split seed, metrics, thresholds, library versions, commit hash).
- **Model selection:** by experiment (E1), not by popularity. Prefer the simpler model if differences are within noise.

---

## 11. Experiments (each produces `experiments/results/eNN_*.csv` + a figure)

| ID | Question | Setup | Key outputs |
|---|---|---|---|
| E1 | Does ML beat baselines? | B0, B1, B2, LR, RF, GBM on identical splits (Febrl4, synthetic-India) | P/R/F1 table |
| E2 | What does blocking buy us? | brute force vs each blocker vs union | pairs completeness, reduction ratio, runtime |
| E3 | Which features matter / does the model over-rely on phone? | permutation importance, drop-field ablations ("hard mode": no phone/email) | importance chart, ablation table |
| E4 | How robust to noise? | noise levels 0–40%, per noise type | F1 vs noise curve |
| E5 | Are probabilities trustworthy; where to set thresholds? | calibration, PR curve, threshold sweep | reliability plot, review-rate vs precision |
| E6 | Does it generalize across datasets? | train on A, test on B (e.g., Febrl → synthetic-India) | cross-dataset F1 |
| E7 | How does it scale? | synthetic 10k/50k/100k/500k per side | runtime, memory, candidate counts. Claim only what is measured. |
| E8 | (optional) Embeddings vs fuzzy vs hybrid | local sentence-transformer similarity as extra feature | F1 delta, cost |
| E9 | (optional) Does human review help? | simulate reviewing k uncertain pairs, retrain, measure | F1 vs k |

---

## 12. Scope

### MVP (must)
CSV upload + validation + profiling; column mapping (with multi-column concat); normalization; blocking; features; one trained calibrated model; three-way decision; one-to-one resolution; results table with per-field explanation; review queue that stores labels; dashboard (counts, confidence histogram, processing time); CSV export; job-based API.

### Should (after MVP works)
Ground-truth upload for real metrics; model comparison page; retrain with review labels; SHAP.

### Could (only with evidence/time)
Embeddings/hybrid, dedup mode, chunked/background workers beyond FastAPI, Excel upload, deployment polish.

### Cut list if time runs short
Embeddings → pgvector → dedup → Celery → SHAP. Never cut: evaluation, blocking, calibration, honest results.

---

## 13. Roadmap — small, independently testable tasks

Each task = one focused change set + tests + short explanation. Ask for approval at the end of each milestone.

### Milestone 0 — Foundations
- **T0.1** Create repo skeleton: `core/`, `experiments/`, `docs/`, `data/` (gitignored), `pyproject`, `ruff`, `pytest`. *Accept:* `pytest` runs (one dummy test), `ruff check` passes.
- **T0.2** `docs/decisions.md` seeded with D1–D12 summaries. *Accept:* file exists, each decision has date + reason.
- **T0.3** `scripts/download_data.py` downloads Febrl via `recordlinkage` and caches to `data/raw/`. *Accept:* script is idempotent, prints row counts and number of true links.

### Milestone 1 — Febrl4 baseline end-to-end (no ML, no web) ← FIRST DELIVERABLE
- **T1.1** CSV loader with encoding/delimiter detection and validation errors. *Accept:* tests for UTF-8, Latin-1, bad header, empty file.
- **T1.2** Profiler returning rows, cols, dtypes, missing %, sample rows as a dict. *Accept:* unit tests on a tiny frame.
- **T1.3** Normalizers: name, phone, email, city, postcode, address (with YAML resources). *Accept:* ≥ 10 table-driven cases per normalizer, including Indian examples.
- **T1.4** Column mapping model + applier (multi-column concat). *Accept:* Febrl `given_name`+`surname` → `name` works.
- **T1.5** Evaluation module: precision/recall/F1/confusion matrix from predicted pair set vs truth set. *Accept:* tested on hand-made examples.
- **T1.6** Baselines B0, B1, B2 using brute-force comparison on Febrl4 (5,000 × 5,000; use `rapidfuzz.process.cdist`). *Accept:* `python -m matchiq.cli baseline --dataset febrl4` prints P/R/F1 and runtime; result saved to `experiments/results/`.

### Milestone 2 — Synthetic data generator
- **T2.1** Noise operators as pure functions with seeds. *Accept:* deterministic tests.
- **T2.2** Generator producing `A.csv`, `B.csv`, `truth.csv` with configurable size/overlap/noise and hard negatives. *Accept:* truth file consistent; eyeball sample check documented.
- **T2.3** Run baselines B0–B2 on synthetic-India; confirm hard mode (no phone/email) is meaningfully harder.

### Milestone 3 — Blocking
- **T3.1** Individual blockers (phone, email, name-key, token with cap, TF-IDF n-gram kNN). *Accept:* unit tests on tiny inputs.
- **T3.2** Union + blocking metrics (completeness, reduction ratio, runtime). *Accept:* reports for Febrl4 and synthetic-India.
- **T3.3** Run E2; choose default blocker set; record in `docs/decisions.md`.

### Milestone 4 — Features, models, calibration, thresholds
- **T4.1** Similarity functions + feature builder with NaN/missing-flag handling. *Accept:* tests including missing-field cases.
- **T4.2** Training set builder from blocked candidates with entity-level split and field dropout. *Accept:* test proving no record leaks across splits.
- **T4.3** Train LR, RF, GBM behind a common interface; run E1. *Accept:* results table with mean ± std.
- **T4.4** Calibration + threshold selection (E5). *Accept:* reliability plot; thresholds saved in model card.
- **T4.5** E3 (importance/ablations) and E4 (noise). *Accept:* result files + figures.
- **T4.6** Resolution (one-to-one) and end-to-end `pipeline.py` + CLI `run`. *Accept:* one command goes from two CSVs + mapping config to results CSV with decisions.

### Milestone 5 — Backend (refine tasks when reached)
FastAPI app; DB models + Alembic; upload + profile endpoints; job endpoints with background runner and progress; results/review/export/analytics endpoints; OpenAPI docs; API tests.

### Milestone 6 — Frontend
Upload → preview/profile → column mapping → run + progress → results table → review queue → dashboard → export.

### Milestone 7 — Review loop & polish
Store labels, show review-based estimates, optional retrain, error states, empty states, loading states, UX polish.

### Milestone 8 — Advanced / scale (only with evidence)
E7 scalability, chunked processing, optional Celery/Redis, embeddings (E8), SHAP, active learning (E9).

### Milestone 9 — Deploy & document
Frontend (Vercel), backend (Render/Railway), DB (Supabase or managed Postgres), env vars, smoke test. README, architecture diagram, ML methodology, experiments write-up, limitations, demo script, interview Q&A.

---

## 14. API Sketch (for Milestone 5)

```
POST /datasets                      multipart upload → {dataset_id, profile}
GET  /datasets/{id}/preview?n=20
POST /jobs                          {dataset_a, dataset_b, mapping, options} → {job_id}
GET  /jobs/{id}                     {status, stage, progress, stats}
GET  /jobs/{id}/results?decision=&page=&page_size=
GET  /jobs/{id}/review-queue
POST /jobs/{id}/reviews             {pair_id, label}
GET  /jobs/{id}/analytics
GET  /jobs/{id}/export?type=matches|non_matches|review|all
```

DB tables (initial): `datasets`, `jobs`, `match_pairs`, `review_labels`, `models`.

Upload constraints for MVP: CSV only, ≤ 50 MB or ≈ 200k rows per file **[DECIDE]**.

---

## 15. Open Decisions for the Team [DECIDE]

| # | Question | Recommended default |
|---|---|---|
| 1 | Team size and deadline (viva/submission date)? | Needed to trim scope; if < 8 weeks, stop after Milestone 7 |
| 2 | Package manager | `uv` |
| 3 | GBM library | implement both behind one interface; pick via E1 |
| 4 | Local DB | Docker Postgres in dev; Supabase only at deploy |
| 5 | Upload limits | CSV, 50 MB |
| 6 | Resolution default | one-to-one |
| 7 | Use NC voter data? | No, unless the team wants a real-data scale test |
| 8 | Demo domain | synthetic Indian customer records (+ Febrl for credibility) |
| 9 | Repo visibility / license | private until cleaned; add license before publishing |
| 10 | Who owns which module? | split so each person can explain their part end to end |

---

## 16. Definition of Done

### MVP done
- Upload two CSVs → profile → map columns → run job → results with MATCH / REVIEW / NON-MATCH, calibrated confidence, per-field explanation → review labels stored → CSV export.
- Evaluation on Febrl4 and synthetic-India with P/R/F1 vs baselines B0–B2, blocking metrics, calibration plot, threshold analysis — all from committed result files.
- `core/` pipeline runs from CLI with no web stack; tests pass; one-command reproduction documented.

### Full done
MVP + noise/generalization/scalability experiments, polished frontend, documented API, deployed demo, README with architecture and honest limitations, and every team member able to explain blocking, features, calibration, thresholds, and evaluation design in an interview.

---

## 17. Guardrails for Documentation & Resume Claims

- Every number in README/slides/resume must link to a file in `experiments/results/`.
- Use bullet templates, filling placeholders only from results:
  - "Built an entity-resolution pipeline (blocking → feature engineering → calibrated GBM) reducing candidate pairs by {RR}% while retaining {PC}% of true matches on {dataset}."
  - "Improved F1 from {B2_F1} (tuned fuzzy baseline) to {ML_F1} on {dataset}; evaluated robustness up to {x}% injected noise."
  - "Designed review-queue thresholds that auto-resolve {y}% of pairs at ≥ {p}% precision."
- State limitations plainly: synthetic data is easier than real data; Febrl is Australian; text-heavy product matching is out of scope for the tabular feature set; no ground truth on user uploads.

---

## 18. Glossary

- **Blocking:** cheap method to generate candidate pairs so we avoid N×M comparisons.
- **Pairs completeness:** share of true matches that survive blocking.
- **Reduction ratio:** share of the N×M comparisons avoided.
- **Hard negative:** non-matching pair that looks similar (same surname + city).
- **Calibration:** making predicted probabilities match observed frequencies.
- **Field dropout:** randomly masking fields in training so the model handles missing data.
- **Fellegi–Sunter:** classical probabilistic record-linkage model (used by Splink).
