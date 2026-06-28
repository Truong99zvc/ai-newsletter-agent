# AINewsletterAgent 🤖📰

> **A production-grade, fully automated AI-powered daily news platform** that scrapes the latest AI content from multiple sources, enriches it, summarizes it with GPT-4o-mini, ranks items by interest profiles using GPT-4.1, and serves them via both a sleek React web dashboard and personalized HTML emails.

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)](https://vite.dev/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-412991?logo=openai&logoColor=white)](https://openai.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-316192?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

---

## 📖 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Backend Services (FastAPI)](#backend-services-fastapi)
- [Frontend Web Dashboard (React + Vite)](#frontend-web-dashboard-react--vite)
- [Database Migrations (Alembic)](#database-migrations-alembic)
- [Dockerized Deployment](#dockerized-deployment)
- [Getting Started](#getting-started)
- [Testing & Quality Assurance](#testing--quality-assurance)

---

## 🌟 Overview

**AINewsletterAgent v2.0** is an autonomous news curation platform designed for AI engineers, researchers, and tech professionals. It replaces noisy feeds with a high-signal briefing tailored specifically to your background and technical interests. 

The pipeline runs automatically to:
1. **Scrape**: Pull fresh items using a **Plugin Scraper Architecture** from 6 major sources (YouTube, OpenAI, Anthropic, arXiv, Google DeepMind, Hugging Face).
2. **Enrich**: Convert documents to Markdown via **Docling** or retrieve full video transcripts using the YouTube API.
3. **Digest**: Generate concise, actionable summaries using **GPT-4o-mini** structured outputs.
4. **Rank**: Score and prioritize articles (0.0 to 10.0) based on your custom profile with **GPT-4.1**.
5. **Deliver**: Serve digests instantly on a **React Dashboard** and dispatch a styled HTML newsletter directly to your inbox.

---

## ⚙️ Key Features

- 🔌 **Plugin Scraper Architecture**: Add new content scrapers by simply inheriting from `BaseScraper` and registering them.
- ⚡ **Concurrent Execution**: Fast parallel scraping using `asyncio` and thread pools.
- 🚀 **FastAPI REST API**: Control pipeline triggers, search digests, view history, and monitor analytics.
- 📊 **Next-Gen Web UI**: Responsive, dark-themed dashboard built with React, Vite, Tailwind-like styling, and charts (Recharts).
- 🛡️ **Resilience & Retry**: Tennacity-backed exponential backoff and circuit-breaking.
- 🗄️ **Alembic Migrations**: Proper database versioning and schema migrations.
- 🐳 **Full-Stack Dockerization**: Multi-stage Docker builds configured with `docker-compose`.
- ⚙️ **Type-Safe Configurations**: Settings validation powered by `Pydantic Settings`.

---

## 🏗️ System Architecture

```
                 ┌────────────────────────────────────────────────────────┐
                 │                  Web Dashboard (React)                 │
                 └───────────────────────────┬────────────────────────────┘
                                             │ HTTP REST / GET / POST
                                             ▼
                 ┌────────────────────────────────────────────────────────┐
                 │                FastAPI Application REST                │
                 └───────────────────────────┬────────────────────────────┘
                                             │
      ┌──────────────────────────────────────┼──────────────────────────────────────┐
      ▼                                      ▼                                      ▼
┌───────────┐                         ┌─────────────┐                        ┌─────────────┐
│ Scrapers  │ (Concurrently executed) │  AI Agents  │ (Structured parsing)   │ Integrations│
└─────┬─────┘                         └──────┬──────┘                        └──────┬──────┘
      ├─ YouTube Channels                    ├─ Digest Agent (GPT-4o-mini)          ├─ smtplib (Gmail)
      ├─ OpenAI Blog                         ├─ Curator Agent (GPT-4.1)             └─ Docling (Converter)
      ├─ Anthropic Blog                      └─ Email Agent (GPT-4o-mini)
      ├─ Google DeepMind Blog
      ├─ Hugging Face Blog
      └─ arXiv AI/ML Papers
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │       PostgreSQL 17       │
                               │  (Alembic version-cont.)  │
                               └───────────────────────────┘
```

---

## 📁 Project Structure

```
ai-newsletter-agent/
├── main.py                         # CLI Entry point
├── pyproject.toml                  # Project metadata & dependencies (uv)
├── alembic.ini                     # Database migration configuration
├── alembic/                        # Database migration scripts
│   └── versions/                   # Migration versions
├── docker/
│   ├── Dockerfile                  # Multi-stage Python app Dockerfile
│   └── docker-compose.yml          # DB, Backend, and Frontend service mesh
├── frontend/
│   ├── Dockerfile                  # Vite static build served with Nginx
│   ├── nginx.conf                  # Nginx reverse proxy configurations
│   ├── package.json                # Frontend package dependencies
│   ├── vite.config.js              # Vite config with API backend proxy
│   ├── index.html                  # Dashboard SPA shell
│   └── src/                        # React code (App, api, pages, styling)
├── app/
│   ├── settings.py                 # Central settings (Pydantic Settings)
│   ├── logging_config.py           # Structured system logging
│   ├── runner.py                   # CLI scraping orchestrator
│   ├── pipeline/                   # Async Orchestrator & State Machine
│   ├── scrapers/                   # BaseScraper & plugin implementations
│   ├── database/                   # SQLAlchemy ORM database models & repositories
│   ├── agent/                      # OpenAI Structured Response wrappers
│   └── profiles/                   # User profiles & interests config
└── tests/                          # 38+ Unit and Integration test suite
```

---

## 🔌 Scraper Plugins

All scrapers extend `BaseScraper` (`app/scrapers/base.py`):
```python
class BaseScraper(ABC):
    @abstractmethod
    def get_source_name(self) -> str: ...
    @abstractmethod
    def get_source_display_name(self) -> str: ...
    @abstractmethod
    def scrape(self, hours: int) -> List[ScrapedItem]: ...
    def enrich(self, item: ScrapedItem) -> ScrapedItem: return item
```
Custom scrapers automatically register inside `ScraperRegistry` (`app/scrapers/registry.py`) via auto-discovery on startup.

---

## ⚡ FastAPI REST API

The FastAPI service exposes endpoints documented via Swagger UI at `/docs`:

- **Health Checks**: `GET /health` (Database state, system version, plugin count)
- **Pipeline Curation**:
  - `POST /api/v1/pipeline/run` — Trigger pipeline asynchronously in the background.
  - `GET /api/v1/pipeline/status/{run_id}` — Get active step-level progress.
  - `GET /api/v1/pipeline/history` — Check logs of previous runs.
- **Digests**:
  - `GET /api/v1/digests` — List, paginate, filter by source, and full-text search digests.
  - `GET /api/v1/digests/{digest_id}` — Detailed view of a summary.
- **Sources**: `GET /api/v1/sources` — Return active scrapers configuration.
- **Analytics**: `GET /api/v1/analytics/summary` — Performance summary.

---

## 🗄️ Database Migrations (Alembic)

Database schema is tracked using **Alembic**. Run migrations to initialize or update the database:

```bash
# Apply migrations to the current database
uv run alembic upgrade head

# Generate a new migration revision
uv run alembic revision --autogenerate -m "description of changes"
```

---

## 🐳 Dockerized Deployment

Run the entire full-stack locally in isolated containers:

```bash
# Build and run Postgres, Backend, and Frontend containers
docker compose -f docker/docker-compose.yml up --build -d

# Verify running services
docker ps
```
- **React Dashboard**: http://localhost (Hosted via Nginx reverse proxying to FastAPI)
- **FastAPI API Swagger Docs**: http://localhost:8000/docs
- **PostgreSQL**: Local port `5432`

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.12+**
- **Node.js 20+**
- **Docker**
- **[uv](https://github.com/astral-sh/uv)** (Python package manager)

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/Truong99zvc/ai-newsletter-agent.git
cd ai-newsletter-agent

# Install dependencies using uv
uv sync
```

### 2. Configure Environments
Copy the environment template and fill in your credentials:
```bash
cp app/example.env app/.env
```
Update `app/.env` with your `OPENAI_API_KEY`, Gmail `APP_PASSWORD`, and PostgreSQL connection configurations.

### 3. Run Locally

```bash
# Start Postgres in Docker
docker compose -f docker/docker-compose.yml up postgres -d

# Initialize schema
uv run alembic upgrade head

# Start Backend API
uv run uvicorn app.api.main:app --reload --port 8000

# Start Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing & Quality Assurance

The codebase comes equipped with a comprehensive test suite (38+ tests) containing unit tests for repositories, agents, scrapers, and integration tests for API endpoints:

```bash
# Run pytest with code coverage tracking
uv run pytest tests/ -v --cov=app --cov-report=term-missing

# Run code style linter and formatter check (Ruff)
uv run ruff check app/ tests/
uv run ruff format --check app/ tests/
```