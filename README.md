<p align="center">
  <img src="https://www.webvoidtechnologies.com/webvoid_logo_tm.png" alt="Webvoid Technologies" height="70">
</p>

# AI NL→SQL & Webpage Generator — Setup Guide

A FastAPI + Jinja2 web app with two AI modules powered by Groq:

1. **Natural Language → SQL** — ask plain-English questions about a College Management database; the app generates, validates, and runs safe read-only SQLite queries.
2. **Screenshot → HTML/CSS** — upload a webpage screenshot and get separated `index.html` + `style.css` with live preview and ZIP download.

Full internals: see [DOCUMENTATION.md](DOCUMENTATION.md).

## Prerequisites

- Python 3.9+
- A Groq API key → https://console.groq.com

## Setup

```bash
# 1. Create and activate the virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and set GROQ_API_KEY

# 4. Create + seed the local SQLite database
python -m app.database.seed
```

## Run

```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000

## Environment variables (.env)

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `GROQ_API_KEY` | Yes | — | Groq API key |
| `GROQ_MODEL` | No | `openai/gpt-oss-120b` | Text model for SQL generation/validation |
| `GROQ_VISION_MODEL` | No | `meta-llama/llama-4-scout-17b-16e-instruct` | Vision model for screenshot analysis |
| `GROQ_TIMEOUT` | No | `60` | Groq request timeout (seconds) |
| `GROQ_MAX_RETRIES` | No | `3` | Groq API retry attempts |
| `SQL_MAX_RETRIES` | No | `5` | SQL generate→validate retry loop limit |
| `DB_PATH` | No | `app/database/college.db` | SQLite file location |
| `DATABASE_URL` | No | `sqlite:///{DB_PATH}` | SQLAlchemy URL (auto-derived) |

## Useful commands

```bash
python -m app.database.seed              # re-create + re-seed college.db
python -m app.database.seed --sql-only   # only regenerate dummy_data.sql
pytest                                   # run tests
curl http://localhost:8000/health        # health check
```

## Pages

| Route | Purpose |
|---|---|
| `/` | Dashboard + service status |
| `/database` | Natural-language SQL query tool |
| `/webpage` | Screenshot → HTML/CSS generator |
| `/schema` | Live schema browser (tables, columns, row counts) |
| `/history` | Query history (in-memory) |
| `/settings` | Configuration status |

## Troubleshooting

| Problem | Fix |
|---|---|
| "GROQ_API_KEY is not configured" | Set the key in `.env` and restart the server |
| SQL queries fail / no tables | Run `python -m app.database.seed` |
| Screenshot module says "fallback" | Your Groq account lacks the vision model — set `GROQ_VISION_MODEL` to a vision-capable model your key can access |
| Port 8000 in use | `lsof -iTCP:8000 -sTCP:LISTEN` then `kill <PID>`, or run with `--port 8001` |

---

<p align="center">
  <strong>Webvoid Technologies</strong><br>
  <a href="mailto:studentprogram@webvoidtechnologies.com">studentprogram@webvoidtechnologies.com</a>
</p>
