# AgentScore System Architecture

## Overview
AgentScore is structured as a decoupled monorepo comprising a Next.js frontend, a FastAPI backend, a background task execution worker, and a sandboxed evaluation engine.

```
+-----------------------------------------------------------------------------------+
|                                 Next.js Frontend                                  |
|   - Team Leader Dashboard (Profile, Submissions, Evaluation Results, Leaderboard) |
|   - Admin Dashboard (50 Teams Mgr, Rubric Config, Freeze Controls, Audit Logs)    |
+-----------------------------------------+-----------------------------------------+
                                          | JSON REST APIs (JWT Bearer / RBAC)
                                          v
+-----------------------------------------------------------------------------------+
|                                  FastAPI Backend                                  |
|   - /api/auth & /api/me (RBAC Authorization)                                      |
|   - /api/submissions (Stage 1 CSV/XLSX & Stage 2 URL Ingestion)                   |
|   - /api/admin (Stage 1 Freeze, Top 20 Qualification, Top 3 Winner Publishing)   |
+---------------------+-----------------------------------+-------------------------+
                      |                                   |
                      v                                   v
+-----------------------------------+   +-------------------------------------------+
|    SQLAlchemy 2.x Database        |   |           Background Job Queue            |
| - Users, Teams, Members           |   | - Evaluation Task Dispatcher              |
| - Submissions & Jobs              |   | - Idempotency & Bounded Retry Manager     |
| - EvaluationResults & Snapshots   |   | - Stage 1 & Stage 2 Worker                |
+-----------------------------------+   +---------------------+---------------------+
                                                              |
                                                              v
                                        +-------------------------------------------+
                                        |        Sandboxed Evaluation Engine        |
                                        | - Stage 1: Deterministic Metrics Calc     |
                                        | - Stage 2: SSRF Guarded HTTP Prober       |
                                        | - 6-Dimension Score Normalizer            |
                                        +-------------------------------------------+
```

## Data Flow
1. **Submission Phase:** Teams submit tabular predictions or agent URLs. Submissions are persisted immutably with SHA-256 integrity hashes.
2. **Queuing Phase:** An `evaluation_job` is created with status `QUEUED`.
3. **Execution Phase:** The worker transitions the job to `EVALUATING`, executes test suites, records execution telemetry (P50/P95 latency, errors, assertions).
4. **Scoring & Aggregation:** Evaluator applies the active versioned rubric, aggregates dimensional scores, and saves `evaluation_results` and `task_results`.
5. **Leaderboard & Freezing:** Admin freezes Stage 1 -> System computes top 20 -> Stage 2 is unlocked for qualified teams -> Admin freezes Final results -> Top 3 winners are published.
