# Atrean Synthetic Data + RAG Platform — Master Plan (Phase 1)

Sources and context
- Assignment: `ai_docs/reference/Atrean Founding Engineer Assignment.docx`
- Summary of requirements: `ai_docs/reference/ReadME`
- Phase prompts: `ai_docs/reference/1_generate_master_plan.txt`, `2_stub_out_project.txt`, `3_fully_code_out_implementation.txt`
- Dataset: `ai_docs/reference/DEMO DATASET.xlsx`
- Workflow reference video: [How to Master AI-Driven Development in Cursor (Step-by-Step Workflow)](https://youtu.be/nO9ly_ZDiUE?si=zfnU5eK7Of9KaqWB)

## 1) Overview and Objectives
Build a backend-heavy platform that ingests a multi-table (financially oriented) relational dataset, enables retrieval-augmented QA across tables, and provides explainable answers by returning both the SQL used and the computed result. Design a minimal multi-agent orchestration for retrieval, analysis, and enrichment, with a simple optional Streamlit UI.

Objectives
- Ingest and model a realistic multi-table dataset with financial tables and time series.
- Provide natural language to SQL (NL→SQL) with contextual grounding and cross-table joins.
- Implement vector-based semantic retrieval to ground SQL planning and improve robustness.
- Return explainable outputs: SQL + answer + context used; log all queries.
- Document a clear multi-agent design; optional simple UI for demo.

## 2) Scope and Key Requirements
Dataset
- ≥5 tables total; ≥2 tables with ≥5,000 rows and ≥10 columns.
- ≥2 financial tables; include time-series columns (monthly/quarterly) and mixed types (numeric, categorical, free-text).
- Use provided `DEMO DATASET.xlsx` or compose from external sources.

Core backend (must-have)
- NL→SQL planning that handles joins and aggregations across tables.
- Semantic retrieval with embeddings to identify relevant tables/columns/rows.
- Explainability: return `{ query: SQL, answer: value, context_used: [...] }`.
- Query logging for debugging/observability.

Agents (design + code)
- Retrieval Agent: retrieves schema/docs/vector context.
- Analysis Agent: reasons about question and validates/clarifies SQL plan.
- Enrichment Agent (optional): pulls external context (e.g., SEC EDGAR, Yahoo Finance).
- Policy Agent (optional): validates queries for safety and compliance.

Frontend (optional bonus)
- Simple Streamlit UI to submit questions and render answer + SQL + context/logs.

## 3) High-Level Architecture
Components
- API Service (FastAPI): endpoints for health, ask(question), schema, logs.
- Database (PostgreSQL): relational store for ingested tables and query logs.
- Vector Index (FAISS initially; switchable to managed vector DB): stores embeddings for schema docs and sampled cell/row/context.
- NL→SQL Planner: prompt/programmatic templates + constrained generation.
- Agent Orchestrator: composes retrieval → planning → execution → analysis (+ enrichment).
- Optional UI (Streamlit): thin client calling API.

Data flow (ask → answer)
1. Receive question in API.
2. Retrieval Agent fetches schema context and relevant vectors (tables/columns/rows/metadata).
3. NL→SQL Planner drafts SQL (joins/aggregations) with guardrails.
4. Execute SQL against Postgres; compute result.
5. Analysis Agent validates and formats explainable output (SQL + answer + context).
6. Persist query log; return response.

## 4) Technology Choices
- Language: Python 3.11+
- Web framework: FastAPI (async, OpenAPI, great DX)
- DB: PostgreSQL (Docker-local), SQLAlchemy/SQLModel for schema + migrations (Alembic)
- Vector store: FAISS (local) with an interface to swap to Pinecone/Weaviate later
- Embeddings: OpenAI text-embedding-3-large or small; alt: HuggingFace bge models
- NL→SQL: OpenAI GPT-4o/GPT-4.1 with structured prompting; fallbacks and validation
- Orchestration: lightweight, custom agents (functions/classes) within the app
- Logging/Observability: structured logs (JSON), request IDs, simple metrics
- Optional UI: Streamlit (single page)

Rationale
- FastAPI + Postgres is a proven combo for data apps
- FAISS is fast for local dev; swappable interface preserves future optionality
- OpenAI embeddings + GPT-based NL→SQL bootstraps accuracy for joins/aggregations

## 5) Conceptual Data Model and ERD Outline
Core tables (to be finalized after exploring `DEMO DATASET.xlsx`)
- `entities` (companies/funds): id, name, sector, region, metadata
- `financials_income` (time-series): entity_id, period, revenue, cogs, gross_profit, opex, ebit, net_income, currency, notes
- `financials_balance` (time-series): entity_id, period, assets, liabilities, equity, cash, receivables, payables, notes
- `transactions` (events): id, entity_id, date, type, amount, currency, counterparty, memo
- `crm_companies` (CRM-like): id, name, stage, owner, created_at, tags, description
- `crm_activities` (CRM-like): id, company_id, date, type, actor, notes
- `query_logs` (internal): id, question, sql, answer_preview, latency_ms, created_at, error, context_refs

Notes
- Ensure at least two tables (e.g., `financials_income`, `financials_balance`) exceed 5,000 rows via period granularity and multiple entities.
- Include free-text (`notes`, `description`) for semantic retrieval tests.

## 6) RAG Workflow Design
- Embedding corpus:
  - Schema cards: table/column descriptions generated from headers and sample data
  - Glossary: derived descriptions of financial metrics and CRM fields
  - Sampled rows/chunks for context grounding
- Retrieval strategy:
  - Hybrid: vector top-k of schema+glossary, plus BM25 on schema text
  - Table/column voting to select join candidates and aggregation targets
- NL→SQL prompting:
  - Input: user question + retrieved schema/context + SQL style guide
  - Output: single SQL query compatible with Postgres; includes CTEs if helpful
  - Guardrails: whitelist table/column names; reject DDL/DML; constrain to SELECT
- Execution and explainability:
  - Execute SQL; compute final scalar or tabular answer
  - Return `{ query, answer, context_used }`; include rows and units when applicable
  - Persist full query log and sampled context references

## 7) Agent Architecture
- Retrieval Agent
  - Inputs: question
  - Outputs: ranked schema docs, candidate tables/columns, context snippets
- Analysis Agent
  - Inputs: question, SQL, execution result
  - Outputs: validated answer, clarifications, human-friendly summary
- Enrichment Agent (optional)
  - Inputs: entity symbols/names, metrics
  - Outputs: supplemental data from SEC/Yahoo; adds references
- Policy Agent (optional)
  - Validates query safety (no writes/ddl), rate limits, budget checks

Interactions
- Orchestrator calls Retrieval → NL→SQL → DB → Analysis → (Enrichment)
- Each step appends to a trace for debugging and the Loom demo

## 8) API Surface (Initial)
- `GET /health` → service status and version
- `POST /ask` { question } → { answer, query, context_used, trace_id }
- `GET /schema` → summarized schema and table stats
- `GET /logs?limit=...` → recent query logs

## 9) Logging, Metrics, and Observability
- Correlate with `trace_id`
- Persist query logs with timing, token usage (if available), and error messages
- Basic counters/histograms for latency; structured JSON logs

## 10) Security and Safety
- No DDL/DML generation; SELECT-only constraint
- Input sanitization and parameterization where relevant
- API keys via environment variables; never commit secrets
- Rate limiting basic guard; optional policy agent for validations

## 11) Development Plan and Milestones
Milestone A — Bootstrap
- Repo setup, env, Docker Postgres, FastAPI skeleton, `.env.example`

Milestone B — Data Ingestion
- Parse `DEMO DATASET.xlsx`; infer schema; create tables; load data; ERD

Milestone C — Embeddings and Retrieval
- Build schema cards and glossary; embed; FAISS index; retrieval APIs

Milestone D — NL→SQL and Execution
- Templates and guardrails; cross-table joins/aggregations; explainable outputs

Milestone E — Agents and Logging
- Retrieval + Analysis (+ optional Enrichment/Policy); persistent query logs

Milestone F — Optional Streamlit UI
- Single page: input box, submit, show answer, SQL, context, trace id, recent logs

Milestone G — Demo and Docs
- Diagram(s) for architecture and agents; curated demo questions; Loom recording per assignment

## 12) Risks and Mitigations
- NL→SQL correctness on complex joins → retrieval-guided table/column selection; few-shot examples; post-run validation
- Dataset scale/performance → indices on join keys/time; pre-aggregations/caching for heavy queries
- Ambiguous questions → follow-up clarification prompts or return of top interpretations
- Vendor lock-in → adapter interfaces for embeddings and vector stores

## 13) Success Criteria (Acceptance)
- Meets dataset constraints (table counts/rows/columns; financial and time-series presence)
- Answers representative finance/CRM questions including joins and YoY growth
- Returns SQL + answer + context_used; logs persist; errors are clear
- Minimal Streamlit UI works as a demo client (optional but targeted)
- Loom video delivered with required sections
