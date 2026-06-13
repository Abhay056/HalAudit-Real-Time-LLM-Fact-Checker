# 🛡️ HalAudit — Real-Time LLM Fact-Checker Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](LICENSE)

A production-grade pipeline that sits between any LLM and the user to automatically audit responses for hallucinations. It extracts atomic factual claims, retrieves evidence via RAG, and uses NLI to label each claim as **Supported**, **Contradicted**, or **Unverifiable** — returning a color-coded audit report with citations.

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────┐
│  LLM Output  │────▶│  Claim Extractor  │────▶│  RAG Retriever  │────▶│  NLI Scorer   │
│  (any text)  │     │  (OpenAI/fallback)│     │  (ChromaDB)     │     │  (DeBERTa)    │
└─────────────┘     └──────────────────┘     └─────────────────┘     └──────┬───────┘
                                                                             │
                    ┌──────────────────┐     ┌─────────────────┐            │
                    │  Dashboard (UI)   │◀────│  Audit Report    │◀───────────┘
                    │  Color-coded      │     │  Trust Score     │
                    └──────────────────┘     └─────────────────┘
```

## ⚡ Tech Stack

| Component | Technology |
|:---|:---|
| **Claim Extraction** | OpenAI API (gpt-4o-mini) with fallback |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) |
| **Vector Store** | ChromaDB |
| **NLI Model** | cross-encoder/nli-deberta-v3-base |
| **API** | FastAPI + Uvicorn |
| **Task Queue** | Redis + ARQ |
| **Rate Limiting** | Redis-backed sliding window |
| **Dashboard** | Vanilla HTML/CSS/JS (dark mode) |
| **Database** | SQLite (audit logs) |

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/Abhay056/HalAudit-Real-Time-LLM-Fact-Checker.git
cd HalAudit-Real-Time-LLM-Fact-Checker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (optional but recommended)
```

### 3. Run

```bash
# Start the API server
uvicorn app.main:app --reload --port 8000

# Open the dashboard
# Visit http://localhost:8000/dashboard
```

### 4. (Optional) Redis for Async Processing

```bash
# Start Redis (Docker)
docker run -d -p 6379:6379 redis:7-alpine

# Start the background worker
python run_worker.py
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/api/v1/audit` | Synchronous audit — returns full report |
| `POST` | `/api/v1/audit/async` | Async audit — returns job ID |
| `GET` | `/api/v1/audit/{job_id}` | Get async job status/result |
| `POST` | `/api/v1/generate-and-audit` | Generate LLM response + audit |
| `POST` | `/api/v1/corpus/ingest` | Add documents to corpus |
| `GET` | `/api/v1/audit/history` | Paginated audit history |
| `GET` | `/api/v1/stats` | Aggregate statistics |
| `GET` | `/api/v1/health` | Health check |

### Example: Audit Text

```bash
curl -X POST http://localhost:8000/api/v1/audit \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Albert Einstein was born in Austria in 1879. He won the Nobel Prize for relativity.",
    "options": {"top_k": 3}
  }'
```

### Example Response

```json
{
  "id": "abc-123",
  "trust_score": 0.5,
  "total_claims": 4,
  "supported_count": 2,
  "contradicted_count": 2,
  "claims": [
    {
      "claim": "Albert Einstein was born in Austria.",
      "label": "Contradicted",
      "confidence": 0.92,
      "evidence": [{"text": "Albert Einstein...born in Germany...", "source": "Physics"}],
      "reasoning": "Evidence contradicts this claim."
    }
  ]
}
```

## 🎨 Dashboard

The dashboard provides three views:

- **Audit View** — Paste text, get color-coded results (green/red/yellow)
- **History View** — Browse past audits with filters
- **Analytics View** — Aggregate trust scores and statistics

## ⚙️ Configuration

| Variable | Default | Description |
|:---|:---|:---|
| `OPENAI_API_KEY` | — | OpenAI API key (optional, enables LLM claim extraction) |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model for claim extraction |
| `REDIS_URL` | `redis://localhost:6379` | Redis URL (optional, enables async) |
| `NLI_MODEL_NAME` | `cross-encoder/nli-deberta-v3-base` | NLI model |
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | Embedding model |
| `SUPPORTED_THRESHOLD` | `0.6` | Min confidence for "Supported" |
| `CONTRADICTED_THRESHOLD` | `0.6` | Min confidence for "Contradicted" |
| `RATE_LIMIT_PER_MINUTE` | `30` | API rate limit |

## 🏋️ Benchmarking

```bash
python benchmarks/latency_benchmark.py
```

Outputs p50/p95/p99 latency metrics and per-component breakdown for 1-20 claims.

## 🐳 Docker

```bash
docker-compose up -d
```

This starts Redis, the API server, and the ARQ worker.

## 📁 Project Structure

```
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py             # Settings (Pydantic BaseSettings)
│   ├── core/
│   │   ├── claim_extractor.py  # LLM-based claim decomposition
│   │   ├── rag_retriever.py    # ChromaDB evidence retrieval
│   │   ├── nli_scorer.py       # NLI model scoring
│   │   └── pipeline.py        # Full audit orchestrator
│   ├── api/v1/router.py       # REST API endpoints
│   ├── api/middleware.py      # Rate limiting middleware
│   ├── queue/                 # ARQ async workers
│   ├── db/                    # Redis + SQLite storage
│   └── corpus/                # Seed data & loader
├── dashboard/                 # Frontend SPA
├── benchmarks/                # Latency benchmarks
├── tests/                     # Unit tests
├── docker-compose.yml
└── requirements.txt
```

## 📝 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file.
