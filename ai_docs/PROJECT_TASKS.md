### Atrean Synthetic Data + RAG Platform — Step-by-Step Task Plan

Source references:
- Assignment: `ai_docs/reference/Atrean Founding Engineer Assignment.docx`
- Dataset: `ai_docs/reference/DEMO DATASET.xlsx`
- Planning prompts:
  - Phase 1: `ai_docs/reference/1_generate_master_plan.txt`
  - Phase 2: `ai_docs/reference/2_stub_out_project.txt`
  - Phase 3: `ai_docs/reference/3_fully_code_out_implementation.txt`
- Context summary: `ai_docs/reference/ReadME`
- Example (structure inspiration): `ai_docs/reference/example_masterplan.md`
- Workflow video: [How to Master AI-Driven Development in Cursor (Step-by-Step Workflow)](https://youtu.be/nO9ly_ZDiUE?si=zfnU5eK7Of9KaqWB)

---

## Phase 0 — Environment & Project Bootstrap

1) Repo hygiene
- Ensure `master` is clean; restore tracked files if needed (docx/xlsx) or add `ai_docs/` to Git.
- Create a new working branch: `feat/atrean-rag-platform`.

2) Tooling setup
- Python 3.11+ and Poetry or uv/pipenv; Node.js LTS if frontend bonus is attempted.
- Postgres (local Docker or cloud instance).
- API keys placeholders: OpenAI/HuggingFace (embeddings), vector DB (FAISS local initially), optional external APIs (SEC, Yahoo Finance).

3) Cursor workflow macros (per video)
- Adopt a loop for each feature: Plan → Stub → Implement → Test → Record Notes → Commit.
- Keep `ai_docs/notes/` for quick ADRs and runbooks (create folder).

Deliverables
- `.env.example` template (keys listed, no secrets).
- `README.md` bootstrap with run instructions.

---

## Phase 1 — Master Plan (Use 1_generate_master_plan.txt)

Goal
- Produce a high-level blueprint tailored to the Atrean assignment requirements in the docx.

Tasks
- Read `ai_docs/reference/ReadME` to extract scope (dataset, RAG, agents, deliverables).
- Generate `ai_docs/masterplan.md` using the prompts in `1_generate_master_plan.txt`.
- Include: objectives, stack, data model, RAG flow, agent roles, milestones, risks.

Acceptance
- Masterplan covers: dataset spec (≥5 tables; 2 financial; 2 tables ≥5k rows; time series), backend-only RAG, NL → SQL, joins/aggregations, explainability (return SQL + answer + context), query logging, multi-agent design, Loom outline.

Artifacts
- `ai_docs/masterplan.md`

---

## Phase 2 — Stub Out Project (Use 2_stub_out_project.txt)

Goal
- Create a minimal but complete skeleton aligned with the masterplan.

Tasks
- Create monorepo or single backend repo structure:
  - `api/` FastAPI endpoints (health, ask, schema, logs).
  - `db/` schema migrations + ORM models.
  - `rag/` embeddings, vector store, retrievers, NL2SQL.
  - `agents/` retrieval, analysis, enrichment, (optional) policy agent.
  - `infra/` docker-compose for Postgres; Makefile/tasks.
  - `scripts/` CLI utilities: load dataset, build embeddings.
  - `ai_docs/` diagrams and ADRs.
- Stub files only: headers, purpose comments, placeholder imports, empty classes/functions, TODOs (no logic).
- Add `README.md` with setup placeholders; `.gitignore`, `pyproject.toml`/`poetry.lock` (minimal).

Acceptance
- App runs `uvicorn` and returns health 200 with version string.
- All modules import successfully; no actual business logic.

Artifacts
- Directory tree with stub files per `2_stub_out_project.txt` guidance.

---

## Phase 3 — Full Implementation (Use 3_fully_code_out_implementation.txt)

Goal
- Implement production-ready core features.

Core features
- Data ingestion: parse `DEMO DATASET.xlsx`; infer schema; create 5+ tables; include ≥2 financial tables; populate Postgres with ≥5k rows in ≥2 tables.
- Embeddings + vector store: create document chunks (schemas, headers, glossaries, sampled rows); store in FAISS; switchable to Pinecone/Weaviate.
- NL → SQL planning: intent classification → table/column retrieval → SQL generation with join/agg handling.
- Execution + explainability: run SQL; return `{ sql, answer, context_used }`.
- Query logging: persist question, sql, latency, error, context.
- Agents: retrieval agent, analysis agent (summarize/reason), enrichment agent (optional SEC/Yahoo), policy agent (optional).

Tasks
- Implement `db/models.py`, migrations, and `scripts/load_dataset.py` for `DEMO DATASET.xlsx`.
- Implement `rag/embeddings.py`, `rag/vector_store.py`, `rag/retriever.py`.
- Implement `rag/nl2sql.py` with prompting/templating and guardrails.
- Implement `api/routes/ask.py` returning answer + SQL + context.
- Implement `agents/orchestrator.py` wiring retrieval → SQL → exec → analysis → enrichment.
- Add logging middleware and persistent query logs table.

Acceptance
- Example questions produce correct SQL and answers for sample cases (sum, YoY growth, joins across 2–3 tables).
- Logs written; errors handled with clear messages.

Artifacts
- Working backend service with documented endpoints.

---

## Phase 4 — Evaluation and Demos

Goal
- Validate functionality and produce a demo.

Tasks
- Create `tests/smoke/` with minimal API tests; `tests/fixtures/` seed data.
- Add `scripts/demo_queries.py` for curated Q&A set.
- Generate ERD diagram and RAG/Agents architecture diagram in `ai_docs/diagrams/`.
- Record 5-min Loom:
  - Problem & approach (0:30)
  - Dataset design & ERD (0:45)
  - RAG workflow demo (1:30)
  - Agent architecture (1:00)
  - Scalability & roadmap (1:00)
  - Code/API walkthrough (0:15)

Acceptance
- All demo queries succeed; diagrams included in repo.

Artifacts
- `ai_docs/diagrams/*.png`, Loom link in `README.md`.

---

## Phase 5 — Hardening & Optional Frontend (Bonus)

- Add simple UI (optional): ask questions and view answers + SQL + context.
- Improve observability: structured logs, request IDs, latency histograms.
- Switch vector DB to managed service; add persistence for FAISS.
- Add caching for repeated queries; warm common aggregations.

---

## Execution Rhythm (from the Cursor video)

For each feature slice:
1. Write goal + acceptance in `ai_docs/notes/feature_name.md`.
2. Plan with the Phase prompt files (`1_generate_master_plan.txt`, `2_stub_out_project.txt`, `3_fully_code_out_implementation.txt`).
3. Stub minimal files and interfaces.
4. Implement incrementally with tight feedback loops.
5. Test via CLI and lightweight API tests.
6. Document what changed; commit with scoped message.

---

## Immediate Next Actions (Day 1)

- Create branch `feat/atrean-rag-platform` and `.env.example`.
- Draft `ai_docs/masterplan.md` using `1_generate_master_plan.txt` and `ai_docs/reference/ReadME`.
- Set up Python project, FastAPI skeleton, and Postgres docker-compose.
- Stub directories and files per Phase 2.
- Sketch ERD based on `DEMO DATASET.xlsx` headers and sheet names.

Once confirmed, we proceed to implement Phase 3 core features.
