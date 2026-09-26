# ReleaseShield

> **Know what breaks before you ship.**

ReleaseShield is an AI-powered Change Impact & Release Readiness Engine built on **IBM Bob 2.0**.  
Before a code change ships, it determines what else in the repository could break, automatically synchronizes affected components, validates the resulting system, and produces auditable release evidence.

---

## The Core Idea

A Git diff tells you what changed.  
**ReleaseShield uses IBM Bob to determine what the change means to the rest of the repository.**

```
Developer changes 1 file
       ↓
IBM Bob analyzes repository-wide impact
       ↓
7 additional hidden dependencies discovered
       ↓
Bob synchronizes all affected files
       ↓
Verification: tests + typecheck + build
       ↓
Release evidence generated
```

---

## Quick Start (5 minutes)

### Prerequisites

- Python 3.11+
- Node.js 18+
- IBM Bob installed and available on `PATH` as `bob`
- Git

### 1. Install dependencies

```bash
python setup.py
```

This installs Python packages, initializes the demo repository as a git repo with the BEFORE state committed, and creates `.env`.

### 2. Start the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

Verify: `curl http://localhost:8000/health`

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**

### 4. Verify the BEFORE state (all tests pass)

```bash
cd demo-repo
pytest tests/ -v
```

Expected: **18 tests, 0 failures**

---

## The Demo (3 minutes)

### Step 1 — Introduce the deliberate incomplete change

```bash
python demo/introduce_change.py
```

This modifies **one file** only:  
`demo-repo/backend/models/payment.py`

Change: `amount = Column(Integer, ...)` → `amount = Column(Numeric(10, 2), ...)`

After this, `pytest tests/ -v` will **fail** — but only because the schema, service, types, and tests are still expecting integer amounts.

### Step 2 — Open ReleaseShield

Go to **http://localhost:3000**

### Step 3 — Click "Analyze Release Impact"

IBM Bob analyzes the repository and discovers:

| Finding | Files |
|---------|-------|
| **Developer changed** | `backend/models/payment.py` (1 file) |
| **Bob discovered** | `backend/schemas/payment.py`, `payment_service.py`, `payments.py`, `Payment.ts`, `payments.ts`, `PaymentCard.tsx`, `test_payments.py`, `fixtures/payments.json` (7–8 files) |

### Step 4 — Click "Synchronize Repository"

Bob performs coordinated multi-file remediation across the entire repository.

### Step 5 — Click "Run Verification"

Executes:
- `pytest tests/ -q` — backend tests
- `tsc --noEmit` — TypeScript typecheck
- `npm test` — frontend component tests

Expected: **all pass**

### Step 6 — View Evidence Report

Release evidence is generated in `artifacts/`:
- `artifacts/impact.json` — structured dependency analysis
- `artifacts/verification.json` — test/build results
- `artifacts/release-report.md` — human-readable release report

### Reset and repeat

```bash
python demo/reset_demo.py
```

This restores the BEFORE state so the demonstration can be run again.

---

## Architecture

```
ReleaseShield Dashboard (Next.js 14)
        ↓ HTTP
ReleaseShield API (FastAPI)
├── /api/analyze      — Git diff + Bob impact analysis
├── /api/impact       — Impact graph
├── /api/remediate    — Bob multi-file sync
├── /api/verify       — Test/build verification
├── /api/report       — Release evidence
└── /api/events       — Audit log / state
        ↓
Git Service           — read-only: branch, commit, diff
IBM Bob Runner        — prompts Bob CLI for analysis + remediation
Impact Service        — parses Bob output → ImpactGraph
Remediation Service   — orchestrates Bob file changes
Verification Engine   — pytest + tsc + jest
Evidence Generator    — impact.json, verification.json, report.md
        ↓
Demo Repository (demo-repo/)
├── backend/models/payment.py      ← deliberately changed
├── backend/schemas/payment.py     ← Bob discovers
├── backend/services/payment_service.py  ← Bob discovers
├── backend/api/payments.py        ← Bob discovers
├── frontend/src/types/Payment.ts  ← Bob discovers
├── frontend/src/api/payments.ts   ← Bob discovers
├── frontend/src/components/PaymentCard.tsx  ← Bob discovers
├── tests/test_payments.py         ← Bob discovers
└── fixtures/payments.json         ← Bob discovers
```

---

## IBM Bob Integration

### Custom Mode

The `release-shield` Bob mode is defined in `.bob/custom_modes.yaml`.

It configures Bob as an enterprise release engineer who:
1. Inspects repository structure and component relationships
2. Traces changed symbols across all dependent files
3. Makes minimum coherent multi-file changes
4. Creates/updates tests for new behavior
5. Documents every change with a reason tied to the original diff

### Bob Workflow

The backend sends Bob structured prompts:

**Impact analysis prompt** (read-only, no changes):
```
Given this Git diff, analyze the repository and identify all files
that will be affected if these changes ship without updates.
```

**Remediation prompt** (makes changes):
```
Given the impact analysis findings, update ALL affected files to
make the repository consistent with the proposed change.
```

**Repair prompt** (self-healing):
```
Verification failed. Here is the output. Make the minimum correction.
```

### Simulation Mode

If Bob is not installed, the backend falls back to static analysis simulation.  
The simulation knows the `Payment.amount` integer→decimal change pattern and produces realistic discovery output.

Set `USE_REAL_BOB=false` in `.env` to force simulation mode.

---

## Project Structure

```
releaseshield/
├── backend/                    # ReleaseShield FastAPI application
│   ├── main.py                 # App entry point
│   ├── config.py               # Settings (pydantic-settings)
│   ├── models.py               # Response models
│   ├── state.py                # In-memory workflow state
│   ├── git_service.py          # Git read-only operations
│   ├── bob_runner.py           # IBM Bob CLI wrapper
│   ├── impact_service.py       # Impact graph construction
│   ├── remediation_service.py  # Bob remediation orchestration
│   ├── verification.py         # Test/build execution
│   ├── evidence.py             # Artifact generation
│   └── routers/                # API route handlers
│       ├── analyze.py          # POST /api/analyze
│       ├── impact.py           # GET /api/impact
│       ├── remediate.py        # POST /api/remediate
│       ├── verify.py           # POST /api/verify
│       ├── report.py           # GET /api/report
│       └── events.py           # GET /api/events, POST /api/reset
│
├── frontend/                   # ReleaseShield Next.js dashboard
│   └── src/
│       ├── app/                # Next.js App Router
│       ├── components/         # UI components
│       └── lib/                # API client + types
│
├── demo-repo/                  # Realistic enterprise demo repository
│   ├── backend/                # FastAPI payment service
│   ├── frontend/               # React/TS payment UI
│   ├── tests/                  # pytest test suite
│   ├── fixtures/               # Test data
│   └── migrations/             # SQL migrations
│
├── demo/
│   ├── introduce_change.py     # Introduce deliberate BEFORE→AFTER change
│   └── reset_demo.py           # Reset to clean BEFORE state
│
├── artifacts/                  # Generated release evidence
│   ├── impact.json
│   ├── verification.json
│   └── release-report.md
│
├── bob_sessions/               # IBM Bob session evidence for hackathon
├── .bob/
│   └── custom_modes.yaml       # release-shield mode definition
├── .env.example                # Environment template
├── requirements.txt            # Python dependencies
└── setup.py                    # Setup/install script
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Capture git diff, run Bob impact analysis |
| `GET` | `/api/impact` | Return structured impact graph |
| `POST` | `/api/remediate` | Run Bob multi-file remediation |
| `POST` | `/api/verify` | Execute verification suite (with self-healing) |
| `GET` | `/api/report` | Return release metrics + artifact paths |
| `GET` | `/api/events` | Return audit log and workflow status |
| `GET` | `/api/state` | Return full workflow state |
| `POST` | `/api/reset` | Reset workflow state |

API docs available at: `http://localhost:8000/docs`

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEMO_REPO_PATH` | `./demo-repo` | Path to demo repository |
| `BOB_EXECUTABLE` | `bob` | Bob CLI binary name |
| `BOB_MODE` | `release-shield` | Bob custom mode |
| `BOB_TIMEOUT` | `120` | Bob execution timeout (seconds) |
| `USE_REAL_BOB` | `true` | Use real Bob vs simulation |
| `MAX_REPAIR_ATTEMPTS` | `2` | Max self-healing attempts |
| `ARTIFACTS_DIR` | `./artifacts` | Evidence output directory |

---

## Self-Healing Loop

When verification fails, ReleaseShield automatically:

1. Captures the full failure output (pytest stderr, tsc errors, etc.)
2. Sends it back to Bob with repository context
3. Bob diagnoses the regression and makes a minimum correction
4. Re-runs verification
5. Repeats up to `MAX_REPAIR_ATTEMPTS` times

Every attempt is logged. Failed attempts are never hidden.

---

## Business Value

ReleaseShield reduces the manual effort required to understand repository-wide change impact.

**Illustrative scenario** (assumptions clearly labeled):
- Team reviews 40 pull requests/week
- Repository-impact analysis: ~15 min/PR  
- = 10 engineering hours/week = **520 hours/year**

This is an illustrative scenario for demonstration purposes, not a measured customer claim.

The real value is risk reduction: catching silent incompatibilities before they reach production.

---

## IBM Bob Hackathon Evidence

Bob session artifacts are stored in `bob_sessions/`.

To record a session:
1. Open IBM Bob IDE with workspace = `demo-repo/`
2. Switch to `release-shield` mode
3. Run the full workflow
4. Export the task report

The key demonstration is:
- **Bob IDE is visible and central**
- **Bob analyzes multiple directories** (backend, frontend, tests)
- **Bob makes actual multi-file edits** (not pre-scripted)
- **Test execution is real** (not mocked)

---

## License

MIT — Built for IBM Bob Hackathon 2024.

*ReleaseShield — Know what breaks before you ship.*
