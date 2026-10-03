# AgentEval (AgentScore) — Multi-Dimensional AI Agent Evaluation & Competition Platform

[![GitHub Repo](https://img.shields.io/badge/GitHub-SaiRishitha29%2FAgentEval-purple.svg?logo=github)](https://github.com/SaiRishitha29/AgentEval)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/Frontend-Next.js%2014-black.svg)](https://nextjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC.svg)](https://tailwindcss.com/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)](#)

**AgentEval** (also known as **AgentScore**) is an enterprise-grade, multi-dimensional evaluation platform designed for conducting high-stakes **AI Agent Building Competitions** (e.g., 18-hour university hackathons with 50 teams, 1–3 members per team).
Official Repository: [https://github.com/SaiRishitha29/AgentEval](https://github.com/SaiRishitha29/AgentEval)

Unlike superficial leaderboard tools that solely measure text generation or single classification metrics, AgentScore evaluates submitted AI systems across six holistic agentic dimensions: **Task Performance**, **Agentic Trajectory Quality**, **Reliability ($pass@1$ & $pass^3$)**, **Output Quality & Groundedness**, **Safety & Constraint Compliance**, and **Operational Latency & Efficiency**.

---

## 🌟 Key Features

### 1. Two-Stage Automated Competition Workflow
- **Stage 1 (Prediction-File Evaluation):** Automated intake, strict CSV/XLSX schema validation, formula-injection sanitization, and deterministic scoring against public and private ground truth test cases.
- **Automatic Top-20 Qualification:** Deterministic ranking engine freezes Stage 1 results and automatically qualifies the top 20 teams into Stage 2.
- **Stage 2 (Live Deployed Agent Testing):** Evaluator safely probes live team HTTP agent endpoints (`/health` & `/predict`) across hidden multi-step scenarios, verifying task assertions, response reliability, timeout thresholds, and safety boundaries.
- **Final Top-3 Winner Selection:** Admin-controlled final result freezing, automated multi-criteria tie-breaking, and official public leaderboard announcement.

### 2. Multi-Dimensional Evaluation Framework
- **Dimension A — Task Performance:** Task Success Rate (TSR), Assertion Satisfaction, Classification (Accuracy, Precision, Recall, F1, ROC-AUC), and Regression (MAE, RMSE, $R^2$).
- **Dimension B — Agentic Behavior:** Tool selection accuracy, argument compliance, trajectory efficiency, and recovery patterns.
- **Dimension C — Reliability:** First-run success ($pass@1$), triple-run deterministic consistency ($pass^3$), and failure rates.
- **Dimension D — Output Quality:** Field completeness, strict schema compliance, groundedness, and instruction following.
- **Dimension E — Safety & Constraint Compliance:** Sandboxed SSRF validation, prompt injection resistance, boundary violation detection, and secret leakage prevention.
- **Dimension F — Operational Efficiency:** P50 & P95 latency profiles, network payload overhead, and timeout compliance.

### 3. Enterprise Security & Anti-Cheating Architecture
- **Complete Private Data Isolation:** Hidden ground-truth test cases and expected labels are completely isolated on the server/evaluator worker and never exposed in client bundles, public APIs, logs, or error responses.
- **Full SSRF Protection for Stage 2 URLs:** Blocks `localhost`, `127.0.0.1`, loopback, IPv6 link-local, RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), cloud metadata services (`169.254.169.254`), and enforces strict DNS revalidation.
- **Role-Based Access Control (RBAC):** Server-side authorization enforcing boundaries between Team Leaders and Administrators.
- **Spreadsheet Formula Injection Defense:** Strips or escapes untrusted formula prefixes (`=`, `+`, `-`, `@`, `\t`, `\r`) in CSV exports.
- **Immutable Audit Trail:** Logs sensitive admin actions (qualification freezes, rubric version changes, credential resets).

---

## 🏗️ Architecture & Technology Stack

```
                                 +-------------------------+
                                 |   Next.js 14 Frontend   |
                                 |  (Tailwind + Lucide +   |
                                 |      Recharts UI)       |
                                 +------------+------------+
                                              |
                                              | REST APIs (JWT / RBAC)
                                              v
                                 +-------------------------+
                                 |     FastAPI Backend     |
                                 | (Auth, Teams, Rubrics,  |
                                 | Submissions, Endpoints) |
                                 +-----+-------------+-----+
                                       |             |
                     +-----------------+             +-----------------+
                     |                                                 |
                     v                                                 v
        +-------------------------+                       +-------------------------+
        |  PostgreSQL / SQLite    |                       |  Redis + Task Worker    |
        | (SQLAlchemy 2.x Models) |                       | (Stage 1 & Stage 2      |
        +-------------------------+                       |    Evaluation Engine)   |
                                                          +------------+------------+
                                                                       |
                                                                       v
                                                          +-------------------------+
                                                          | Evaluator & SSRF Guard  |
                                                          |  - CSV/XLSX Validator   |
                                                          |  - Multi-Run API Prober |
                                                          |  - Score Normalization  |
                                                          +-------------------------+
```

### Stack Components
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide React, Recharts, React Hook Form, Zod.
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, Pandas, NumPy, Scikit-learn, Passlib/Bcrypt, PyJWT, HTTPX.
- **Storage & Database:** PostgreSQL (Production) / SQLite (Zero-config local dev), Local / S3-compatible private object storage.
- **Asynchronous Execution:** Background evaluation queue with graceful failure recovery, bounded retries, and cancellation.

---

## 📁 Repository Structure

```
AgentScore/
├── README.md                          # Complete project documentation
├── .env.example                       # Environment template
├── .gitignore                         # Git exclusion rules
├── docker-compose.yml                 # Full stack containerization
├── docs/                              # Comprehensive technical specifications
│   ├── architecture.md               # System architecture & data flow
│   ├── evaluation-framework.md        # Mathematical formulas & dimensions
│   ├── api-contract.md                # Stage 2 agent HTTP specification
│   ├── deployment.md                  # Production deployment guide
│   └── security.md                    # Threat model & SSRF defense
├── backend/                           # FastAPI Application
│   ├── app/
│   │   ├── api/                       # REST routes (auth, teams, admin, submissions)
│   │   ├── core/                      # Config, security, SSRF validator, JWT
│   │   ├── db/                        # Database session & engine
│   │   ├── models/                    # SQLAlchemy database models
│   │   ├── schemas/                   # Pydantic validation schemas
│   │   ├── services/                  # Business logic & seed generator
│   │   ├── evaluation/                # Stage 1 & Stage 2 evaluation engines
│   │   ├── workers/                   # Background job queue & worker
│   │   └── main.py                    # FastAPI entrypoint
│   ├── tests/                         # Unit, integration & security test suites
│   ├── Dockerfile                     # Backend container file
│   ├── Dockerfile.worker              # Worker container file
│   └── requirements.txt               # Python dependencies
├── frontend/                          # Next.js 14 Web Application
│   ├── app/                           # App router pages (Landing, Login, Dashboard, Admin, etc.)
│   ├── components/                    # Reusable UI components, charts, modals
│   ├── lib/                           # API client, state, auth helpers
│   ├── types/                         # TypeScript interfaces
│   ├── public/                        # Static assets & logos
│   ├── Dockerfile                     # Frontend container file
│   └── package.json                   # Frontend dependencies
├── evaluator/                         # Standalone evaluation & metric modules
│   ├── stage1/                        # CSV/XLSX parsing & tabular scoring
│   ├── stage2/                        # HTTP client, agent health, multi-run prober
│   ├── metrics/                       # TSR, pass@1, pass^3, accuracy, F1, latency
│   └── safety/                        # SSRF sandbox & adversarial test harness
├── datasets/                          # Benchmark datasets
│   ├── sample_training.csv            # Public training set
│   ├── sample_public_test.csv         # Public test input
│   ├── sample_hidden_test.csv         # Private ground-truth dataset (server-only)
│   └── sample_submission.csv          # Reference prediction submission
└── scripts/                           # Utility scripts
    ├── seed_data.py                   # Generates 50 teams & competition rubric
    ├── run_mock_agent.py              # Mock deployed agent for Stage 2 testing
    └── run_tests.bat / .sh            # Automated test runner
```

---

## ⚡ Quickstart & Local Setup

### Prerequisites
- **Python:** 3.11 or higher
- **Node.js:** 18.x or higher (v20+ recommended)
- **Git:** Installed and configured
- *(Optional)* Docker and Docker Compose

---

### Method 1: Instant Local Setup (Zero-Config Development Mode)

#### 1. Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database & seed 50 competition teams + sample data
python -m app.services.seed_data

# Start backend API server (runs on http://localhost:8000)
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
# In a new terminal, navigate to frontend
cd frontend

# Install Node dependencies
npm install

# Start Next.js development server (runs on http://localhost:3000)
npm run dev
```

Visit **http://localhost:3000** in your browser.

---

### Default Credentials (Generated by Seeder)

| Role | Username / Identifier | Password | Access / Description |
|---|---|---|---|
| **Administrator** | `admin@agentscore.org` | `AdminSecret2026!` | Full Admin Dashboard, Team Management, Freezing, Rubrics |
| **Team 1 Leader** | `team_01` (or `leader01@team01.edu`) | `Team01Pass2026!` | Team Dashboard, Stage 1 & Stage 2 Submissions, Team Results |
| **Team 2 Leader** | `team_02` (or `leader02@team02.edu`) | `Team02Pass2026!` | Pre-registered Team 2 Leader |
| *Teams 3 to 50* | `team_XX` | `TeamXXPass2026!` | Standard credentials for all 50 pre-registered teams |

---

### Method 2: Containerized Setup (Docker Compose)

To launch the full production-like environment with PostgreSQL, Redis, FastAPI backend, Worker, and Next.js frontend:

```bash
docker-compose up --build
```

---

## 📊 Evaluation Formulas & Rubrics

### Stage 1 (Tabular Prediction & Trajectory Traces)
$$\text{Task Success Rate (TSR)} = \frac{\text{Correct Predictions}}{\text{Total Test Items}} \times 100$$

$$\text{Stage 1 Score} = 0.40 \cdot \text{Accuracy} + 0.20 \cdot \text{Tool Acc} + 0.15 \cdot \text{Constraints} + 0.15 \cdot \text{Quality} + 0.10 \cdot \text{Efficiency}$$

### Stage 2 (Live Deployed Agent Testing)
$$pass@1 = \frac{\text{Tasks Successful on Run 1}}{\text{Total Tasks}} \times 100$$

$$pass^3 = \frac{\text{Tasks Successful on All 3 Consecutive Runs}}{\text{Total Tasks}} \times 100$$

$$\text{Safety Score} = 100 \times \left(1 - \frac{\text{Unsafe Actions Detected}}{\text{Adversarial Probes}}\right)$$

### Final Competition Score
$$\text{Final Score} = (0.60 \times \text{Stage 1 Score}) + (0.40 \times \text{Stage 2 Score})$$

---

## 🧪 Running Automated Tests

AgentScore includes a comprehensive test suite covering Unit, Integration, and Security scenarios.

```bash
cd backend
pytest tests/ -v
```

### Test Coverage Highlights:
- ✅ Metric formulas (TSR, F1, MAE, $pass@1$, $pass^3$)
- ✅ Score normalization and deterministic multi-key tie-breaking
- ✅ File upload validation (CSV/XLSX schema, size, malicious formulas)
- ✅ SSRF blocking (localhost, RFC1918 subnets, cloud metadata)
- ✅ Top-20 automatic qualification & Stage 1 lock logic
- ✅ Final Top-3 winner publishing logic

---

## 🔒 Security & Deployment Checklist

- [x] Passwords hashed with secure cryptographic algorithms (Bcrypt / PBKDF2).
- [x] JWT tokens with configurable expiration and secure HTTP headers.
- [x] Server-side role authorization on every protected API endpoint.
- [x] Complete hidden test dataset isolation from team-facing responses.
- [x] Multi-layer SSRF filter on all submitted Stage 2 URLs.
- [x] Formula injection protection on all CSV exports.
- [x] Detailed immutable audit logs for all sensitive administrative actions.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
