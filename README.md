# AINewsletterAgent 🤖📰

> **A fully automated, AI-powered daily news digest agent** that scrapes the latest AI content from YouTube channels, OpenAI, and Anthropic — then intelligently summarizes, ranks, and delivers a personalized newsletter straight to your inbox every day.

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-412991?logo=openai&logoColor=white)](https://openai.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-316192?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)](https://www.sqlalchemy.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Customization](#customization)
- [Tech Stack](#tech-stack)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**AINewsletterAgent** is an end-to-end autonomous pipeline that keeps you up-to-date with the rapidly evolving AI landscape — without any manual effort. Each day, the agent:

1. **Scrapes** the latest articles and videos from trusted AI sources (OpenAI Blog, Anthropic Blog, YouTube channels).
2. **Processes** raw content — fetching full article text as Markdown and extracting YouTube video transcripts.
3. **Summarizes** every piece of content into a concise, actionable digest using GPT-4o-mini.
4. **Ranks** digests based on your personal interest profile using GPT-4.1 as an AI curator.
5. **Composes** a beautiful, personalized newsletter and delivers it to your inbox via email.

This project is ideal for AI engineers, researchers, and enthusiasts who want a daily, signal-rich briefing tailored to their specific interests — cutting through the noise automatically.

---

## Features

- 🕵️ **Multi-source scraping** — Pulls from OpenAI RSS, Anthropic (news + research + engineering), and YouTube channel feeds simultaneously.
- 📝 **Full content extraction** — Uses [Docling](https://github.com/DS4SD/docling) to convert full web articles to clean Markdown, not just descriptions.
- 🎬 **YouTube transcript extraction** — Fetches full video transcripts via `youtube-transcript-api`, with optional proxy support.
- 🤖 **AI-powered digests** — GPT-4o-mini reads each article and writes a compelling, concise 2–3 sentence summary with a fresh title.
- 🎯 **Personalized curation** — GPT-4.1 acts as an expert AI news curator, scoring and ranking all digests based on your user profile (interests, expertise level, preferences).
- 📧 **Rich HTML email delivery** — Sends a polished, mobile-friendly HTML email with ranked articles, summaries, and "Read more" links.
- 🗄️ **Persistent PostgreSQL storage** — All scraped content and generated digests are stored to avoid reprocessing and enable historical queries.
- 🐳 **Docker-ready database** — One-command PostgreSQL setup with Docker Compose.
- ⚙️ **Configurable pipeline** — Customize the time window (`--hours`) and number of top articles (`--top_n`) from the command line.
- 🔄 **Idempotent operations** — Duplicate detection on all inserts ensures no repeated content even across multiple runs.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Daily Pipeline                              │
│                                                                     │
│  ┌──────────┐   ┌────────────────┐   ┌────────────┐   ┌─────────┐  │
│  │ Scrapers │──▶│   Processors   │──▶│  AI Agents │──▶│  Email  │  │
│  └──────────┘   └────────────────┘   └────────────┘   └─────────┘  │
│       │                 │                   │               │       │
│  YouTube RSS      Fetch Markdown       DigestAgent     EmailAgent   │
│  OpenAI  RSS      Get Transcripts     CuratorAgent    send via SMTP │
│  Anthropic RSS    Store to DB         GPT-4o-mini      Gmail SSL    │
│                                        GPT-4.1                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   PostgreSQL DB     │
                    │ - youtube_videos   │
                    │ - openai_articles  │
                    │ - anthropic_articles│
                    │ - digests          │
                    └────────────────────┘
```

The pipeline runs as a **5-step sequential process**:

| Step | Module | Description |
|------|--------|-------------|
| 1 | `runner.py` | Scrape all sources and store new content to DB |
| 2 | `process_anthropic.py` | Fetch full Anthropic article pages as Markdown |
| 3 | `process_youtube.py` | Fetch YouTube video transcripts |
| 4 | `process_digest.py` | Generate AI summaries for all new content |
| 5 | `process_email.py` | Rank, compose, and send the newsletter |

---

## Project Structure

```
AI-Agent/
├── main.py                         # Entry point — runs the full pipeline
├── pyproject.toml                  # Project metadata and dependencies (uv)
├── docker/
│   └── docker-compose.yml          # PostgreSQL service definition
└── app/
    ├── config.py                   # YouTube channel IDs to monitor
    ├── runner.py                   # Orchestrates all scrapers
    ├── daily_runner.py             # Full 5-step pipeline with logging
    ├── example.env                 # Environment variable template
    │
    ├── scrapers/                   # Data ingestion layer
    │   ├── youtube.py              # YouTube RSS + transcript fetcher
    │   ├── openai.py               # OpenAI blog RSS scraper
    │   └── anthropic.py            # Anthropic blog RSS scraper (3 feeds)
    │
    ├── agent/                      # AI agent layer (OpenAI API)
    │   ├── digest_agent.py         # Summarizes content with GPT-4o-mini
    │   ├── curator_agent.py        # Ranks digests with GPT-4.1
    │   └── email_agent.py          # Writes personalized email intro
    │
    ├── services/                   # Business logic / pipeline steps
    │   ├── email.py                # SMTP sender + Markdown-to-HTML renderer
    │   ├── process_anthropic.py    # Fills in Anthropic article Markdown
    │   ├── process_youtube.py      # Fills in YouTube transcripts
    │   ├── process_digest.py       # Creates digests for unprocessed articles
    │   ├── process_curator.py      # Standalone curation service
    │   └── process_email.py        # Generates and sends email digest
    │
    ├── database/                   # Data persistence layer
    │   ├── models.py               # SQLAlchemy ORM models
    │   ├── connection.py           # DB engine and session factory
    │   ├── repository.py           # Data access layer (CRUD operations)
    │   └── create_tables.py        # Schema initializer
    │
    └── profiles/
        └── user_profile.py         # Your personal interests and preferences
```

---

## How It Works

### Step 1 — Scraping

The **scrapers** pull content from three sources using their RSS/Atom feeds:

- **OpenAI** (`openai.com/news/rss.xml`) — News and announcements.
- **Anthropic** — Three separate feeds: News, Research, and Engineering, deduplicated by GUID.
- **YouTube** — Configured channel IDs (via `app/config.py`). Short videos are automatically skipped. Uses the `youtube-transcript-api` library with optional Webshare proxy support for transcript fetching.

All new items are stored to PostgreSQL. Duplicate detection prevents re-insertion across runs.

### Step 2 & 3 — Content Enrichment

- **Anthropic articles** that lack a `markdown` field are fetched in full using **Docling**, a state-of-the-art document converter that produces clean Markdown from web pages.
- **YouTube videos** without a transcript have their transcript fetched and stored.

### Step 4 — AI Digest Generation

The `DigestAgent` (powered by **GPT-4o-mini**) processes every new article:
- Reads up to 8,000 characters of content.
- Outputs a structured `DigestOutput` with a concise **title** (5–10 words) and a **2–3 sentence summary** focused on actionable insights — no marketing fluff.
- Structured output is enforced via **Pydantic** models and OpenAI's structured response parsing.

### Step 5 — Curation, Composition & Delivery

1. **`CuratorAgent`** (GPT-4.1) — Reads all recent digests alongside your user profile, then assigns each article a relevance **score (0–10)** and a **rank**. Ranking factors include: alignment with your interests, technical depth, novelty, and actionability.
2. **`EmailAgent`** (GPT-4o-mini) — Writes a warm, personalized greeting and introduction paragraph previewing the top articles.
3. The final email is rendered as **both plain-text and styled HTML** (responsive, mobile-friendly) and sent via Gmail SMTP using an App Password.

---

## Prerequisites

- **Python 3.12+**
- **[uv](https://github.com/astral-sh/uv)** — fast Python package manager (recommended)
- **Docker & Docker Compose** — for the PostgreSQL database
- **OpenAI API Key** — for GPT-4o-mini and GPT-4.1
- **Gmail account** with an [App Password](https://support.google.com/accounts/answer/185833) enabled

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Truong99zvc/ai-newsletter-agent.git
cd ai-newsletter-agent
```

### 2. Install dependencies

Using `uv` (recommended):

```bash
uv sync
```

Or using `pip`:

```bash
pip install -e .
```

### 3. Start the PostgreSQL database

```bash
docker compose -f docker/docker-compose.yml up -d
```

Wait for the health check to pass (usually a few seconds). Verify with:

```bash
docker ps
```

### 4. Set up environment variables

Copy the example `.env` file and fill in your credentials:

```bash
cp app/example.env app/.env
```

Then edit `app/.env` (see [Configuration](#configuration) below).

### 5. Initialize the database schema

```bash
uv run python -m app.database.create_tables
```

---

## Configuration

Edit `app/.env` with your actual credentials:

```env
# Required: Your OpenAI API key for GPT models
OPENAI_API_KEY=sk-...

# Required: Gmail address and App Password for sending emails
MY_EMAIL=your.email@gmail.com
APP_PASSWORD=xxxx xxxx xxxx xxxx

# PostgreSQL connection (defaults work with Docker Compose)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ai_news_aggregator
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Optional: Webshare proxy credentials for YouTube transcript fetching
# PROXY_USERNAME=
# PROXY_PASSWORD=
```

> **Note on Gmail App Password:** Go to your Google Account → Security → 2-Step Verification → App Passwords. Generate a password for "Mail". Do **not** use your regular Gmail password.

### Configuring YouTube Channels

Edit `app/config.py` to add or change YouTube channel IDs:

```python
YOUTUBE_CHANNELS = [
    "UCawZsQWqfGSbCI5yjkdVkTA",  # Matthew Berman
    # "UCn8ujwUInbJkBhffxqAPBVQ",  # Dave Ebbelaar
    # Add more channel IDs here...
]
```

To find a channel ID, go to the channel's page → view page source → search for `"channelId"`.

### Customizing Your User Profile

Edit `app/profiles/user_profile.py` to personalize the curation to your interests:

```python
USER_PROFILE = {
    "name": "Your Name",
    "title": "Your Title",
    "background": "Brief description of your background",
    "interests": [
        "Large Language Models (LLMs) and their applications",
        "AI agent architectures and frameworks",
        # Add or remove interests...
    ],
    "preferences": {
        "prefer_practical": True,
        "prefer_technical_depth": True,
        "prefer_research_breakthroughs": True,
        "prefer_production_focus": True,
        "avoid_marketing_hype": True,
    },
    "expertise_level": "Advanced",  # Beginner / Intermediate / Advanced
}
```

The `CuratorAgent` uses this profile to score every article and prioritize what matters most to you.

---

## Usage

### Run the full daily pipeline

```bash
# Default: last 24 hours, top 10 articles
uv run python main.py

# Custom: last 48 hours, top 5 articles
uv run python main.py 48 5
```

### Run individual pipeline steps

Each service module can also be run independently for testing or debugging:

```bash
# Step 1: Scrape all sources
uv run python -m app.runner

# Step 2: Enrich Anthropic articles with full Markdown
uv run python -m app.services.process_anthropic

# Step 3: Fetch YouTube transcripts
uv run python -m app.services.process_youtube

# Step 4: Generate AI digests
uv run python -m app.services.process_digest

# Step 5: Curate (rank only, no email)
uv run python -m app.services.process_curator

# Step 5: Generate and send the email digest
uv run python -m app.services.process_email
```

### Schedule daily execution

To run automatically every day, add a cron job (Linux/macOS):

```bash
# Run every day at 7:00 AM
0 7 * * * cd /path/to/AI-Agent && uv run python main.py >> /var/log/ai-news.log 2>&1
```

On Windows, use **Task Scheduler** to run `uv run python main.py` on a daily schedule.

---

## Tech Stack

| Category | Technology |
|---|---|
| **Language** | Python 3.12+ |
| **Package Manager** | [uv](https://github.com/astral-sh/uv) |
| **AI Models** | OpenAI GPT-4.1 (curation), GPT-4o-mini (summarization, email) |
| **Web Scraping** | `feedparser`, `requests`, `beautifulsoup4` |
| **Document Conversion** | [Docling](https://github.com/DS4SD/docling) |
| **YouTube** | `youtube-transcript-api` |
| **Database** | PostgreSQL 17 |
| **ORM** | SQLAlchemy 2.0 |
| **Data Validation** | Pydantic v2 |
| **Email** | Python `smtplib` + Gmail SMTP SSL |
| **Markdown** | `markdown`, `markdownify` |
| **Infrastructure** | Docker Compose |
| **Config** | `python-dotenv` |

---

## Contributing

Contributions are welcome! Here are some ideas for enhancements:

- **Add more sources** — arXiv, Hugging Face blog, Google DeepMind, etc.
- **Add a web dashboard** — A simple UI to browse digests and tweak your profile.
- **Support multiple user profiles** — Send personalized newsletters to multiple recipients.
- **Add scheduling** — Built-in cron/APScheduler integration instead of relying on OS cron.
- **Add retry logic** — More resilient scraping with exponential backoff.

To contribute:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and write clear commit messages.
4. Open a Pull Request describing what you changed and why.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for details.

---

<div align="center">
  <p>Built with ❤️ for AI enthusiasts who want signal, not noise.</p>
</div>