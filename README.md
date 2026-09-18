# Rank & Rent Research System

An AI-powered research pipeline that automates the Flat Fee Mastery / Digital Landlords rank-and-rent methodology. Built with CrewAI, FastAPI, and a real-time streaming UI.

SEO data comes from **Ahrefs** (Keywords Explorer + Site Explorer). This project previously used Semrush; see [Migrated from Semrush](#migrated-from-semrush) if you are updating an existing deploy.

## What It Does

Runs a 6-phase research pipeline to find and validate rank-and-rent opportunities:

- **Phase 1 — Keyword Research**: Builds a master keyword list for your niche using Ahrefs (cached for known niches — no API units used)
- **Phase 2 — City Selection**: Finds qualifying cities in your target state (volume ≥30, CPC $0.01–$4.99). Stops after 3 passing cities to conserve units
- **Phase 3 — Competitor Identification**: Identifies the top 3 Google Maps 3-pack competitors across 10+ keyword searches
- **Phase 4 — Due Diligence**: Scores each competitor on 4 metrics (domain age, backlinks, content depth, organic page 1 presence) and delivers a GO/NO-GO verdict
- **Phase 5 — Prospect List**: Finds 7–12 businesses already paying for advertising — exportable as a styled Excel call sheet
- **Phase 6 — Ad Copy**: Writes complete Google Smart Campaign + Facebook Lead Ad copy ready to paste into the ad platforms

## Tech Stack

- **Backend**: FastAPI + Server-Sent Events (real-time streaming)
- **AI Pipeline**: CrewAI (multi-agent, sequential process)
- **LLM**: Claude Sonnet (Anthropic)
- **Data**: Ahrefs API v3 (keywords, volume/CPC, domain metrics, backlinks), Serper API (Google Maps + Ads search)
- **Tools**: WHOIS domain age, BeautifulSoup content analyzer, persistent city result cache
- **Export**: openpyxl Excel generation

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/JasonAndersen11/rank-rent-crew.git
cd rank-rent-crew
```

### 2. Install Python dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example file and fill in real keys (never commit `.env`):

```bash
cp .env.example .env
```

| Variable | Required for | How to get it |
| --- | --- | --- |
| `AHREFS_API_KEY` | Keyword research, city volume/CPC, domain metrics, backlinks | Ahrefs workspace **Account settings → API keys**. Use an **API v3** key (Bearer token). Owners/admins only. Docs: [Ahrefs API introduction](https://docs.ahrefs.com/api/docs/introduction.md) |
| `ANTHROPIC_API_KEY` | CrewAI agents (Claude) | [Anthropic console](https://console.anthropic.com/settings/keys) |
| `SERPER_API_KEY` | Google Maps 3-pack + Ads search | [serper.dev](https://serper.dev) |

Do **not** put a live API key in git, docs, or examples. Placeholder names only.

### 4. Run the app

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000](http://localhost:8000). Confirm keys loaded:

```bash
curl -s http://localhost:8000/api/health
# expect: "ahrefs": true, "anthropic": true, "serper": true
```

## Ahrefs API vs Ahrefs MCP

This app’s **runtime pipeline** calls **Ahrefs API v3** with `AHREFS_API_KEY`. Ahrefs does not allow using the hosted MCP server as a general-purpose HTTP API from scripts.

For **Cursor / Grok Bot** interactive research (keywords, backlinks, rankings, site health), use the **Ahrefs MCP** connector already available on the owner account (plugin: *Ahrefs — research keywords, backlinks, rankings, site health*).

- Remote MCP URL: `https://api.ahrefs.com/mcp/mcp`
- Example Cursor config: [`.cursor/mcp.json.example`](.cursor/mcp.json.example)
- MCP setup: [Getting started with Ahrefs MCP](https://help.ahrefs.com/en/articles/13913559-getting-started-with-ahrefs-mcp)
- MCP keys are tagged with an `MCP` scope. They are **not** a drop-in replacement for `AHREFS_API_KEY` in this FastAPI/CrewAI app.

## Migrated from Semrush

If an existing deploy still has Semrush env vars, rename them and issue a new Ahrefs key. Semrush keys cannot be reused.

| Old (Semrush) | New (Ahrefs) |
| --- | --- |
| `SEMRUSH_API_KEY` | `AHREFS_API_KEY` |

Code, tool names, UI copy, and health checks no longer read `SEMRUSH_API_KEY`. After migrating, remove the old Semrush key from your host so it cannot be used by mistake.

### Feature mapping

| Pipeline need | Previous Semrush report | Ahrefs API v3 |
| --- | --- | --- |
| Related / seed keywords | `phrase_related` | `GET /v3/keywords-explorer/matching-terms` |
| National volume + CPC | `phrase_this` | `GET /v3/keywords-explorer/overview` |
| City keyword check | `phrase_this` on `[keyword] [city] [ST]` | same overview endpoint |
| Domain organic presence | `domain_ranks` | `GET /v3/site-explorer/metrics` (+ domain rating) |
| Backlink totals | `backlinks_overview` | `GET /v3/site-explorer/backlinks-stats` |

PASS/FAIL city thresholds and competitor scoring bands are unchanged.

### Gaps vs Semrush (no leftover Semrush hooks)

- **Competition (0–1)** → Ahrefs **Keyword Difficulty (0–100)**. Volume + CPC still drive city PASS/FAIL.
- **DoFollow / NoFollow counts** are not on `backlinks-stats`. Scoring still uses **live backlink total** and **referring domains** (same 0–10 / 98+ bands).
- **Semrush Rank** → **Domain Rating** + **Ahrefs Rank**. Zero organic keywords/traffic is still a green flag (replaces Semrush `ERROR 50`).

CPC from Ahrefs is in **USD cents** and is converted to dollars before thresholds (`221` → `$2.21`).

## Verify

```bash
# unit tests (mocked Ahrefs HTTP — no live key required)
python -m unittest tests.test_ahrefs -v

# health after setting .env
curl -s http://localhost:8000/api/health
```

Smoke-test the UI: open `/`, confirm the How It Works strip says **Ahrefs · 5–7 terms**, then run a cached niche (`concrete`, `tree service`, or `fencing`) so Phase 1 does not spend Ahrefs units. Phase 2+ will call Ahrefs unless the city result is already in `city_result_cache.json`.
