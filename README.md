# Rank & Rent Research System

An AI-powered research pipeline that automates the Flat Fee Mastery / Digital Landlords rank-and-rent methodology. Built with CrewAI, FastAPI, and a real-time streaming UI.

## Quick start (Mac)

1. **Double-click `Start RankRent.command`** in this folder.
   - The first time, it sets up Python and installs everything (a few minutes). If you don't have Python 3.10–3.13, it opens the download page.
   - If your API keys aren't in yet, it opens `.env` in TextEdit. Paste your keys after the `=` signs, save, and double-click again.
2. The app opens in your browser at **http://localhost:8000**.
3. Pick a niche and a state, then click **Run research**.
4. To stop the app, close the Terminal window that opened (or press Ctrl+C in it).

If macOS says the file can't be opened, right-click it, choose **Open**, then click **Open** again. You only need to do this once.

## What It Does

Runs a 6-phase research pipeline to find and validate rank-and-rent opportunities:

- **Phase 1 — Keyword Research**: Builds a master keyword list for your niche using Semrush (cached for known niches — no API credits used)
- **Phase 2 — City Selection**: Finds qualifying cities in your target state (volume ≥30, CPC $0.01–$4.99). Stops after 3 passing cities to conserve credits
- **Phase 3 — Competitor Identification**: Identifies the top 3 Google Maps 3-pack competitors across 10+ keyword searches
- **Phase 4 — Due Diligence**: Scores each competitor on 4 metrics (domain age, backlinks, content depth, organic page 1 presence) and delivers a GO/NO-GO verdict
- **Phase 5 — Prospect List**: Finds 7–12 businesses already paying for advertising — exportable as a styled Excel call sheet
- **Phase 6 — Ad Copy**: Writes complete Google Smart Campaign + Facebook Lead Ad copy ready to paste into the ad platforms

If a state has no qualifying cities, the app suggests the next untried state in this order: FL, TX, GA, NC, AZ, TN, SC, AL, LA, NV, VA, OK, UT, AR, MS.

## Tech Stack

- **Backend**: FastAPI + Server-Sent Events (real-time streaming)
- **AI Pipeline**: CrewAI (multi-agent, sequential process)
- **LLM**: Claude Sonnet (Anthropic)
- **Data**: Semrush API, Serper API (Google Maps + Ads search)
- **Tools**: WHOIS domain age, BeautifulSoup content analyzer, persistent city result cache
- **Export**: openpyxl Excel generation

## Manual setup (any OS)

```bash
git clone https://github.com/JasonAndersen11/SEO-Scout-Market-Research-Tool.git
cd SEO-Scout-Market-Research-Tool
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then add your API keys
uvicorn main:app --port 8000
```

Open http://localhost:8000. Check that your keys loaded at http://localhost:8000/api/health.

## Adding markets to the dashboard

The Market history cards, market map and CPC chart all read from the `MARKETS` list near the top of the script in `static/index.html`. Add one line per market you want to show:

```js
{ niche: 'tree service', city: 'Monroe', state: 'LA', volume: 140, cpc: 2.80, verdict: 'PASS' },
```
