import os
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

SEMRUSH_BASE = "https://api.semrush.com/"
SEMRUSH_ANALYTICS = "https://api.semrush.com/analytics/v1/"

# Actual column names returned by Semrush API (not the internal codes):
# phrase_this / phrase_related: Keyword | Search Volume | CPC | Competition
# domain_ranks: Domain | Rank | Organic Keywords | Organic Traffic | ...
# backlinks_overview: total | domains_num | follows_num | nofollows_num


def _api_key():
    return os.getenv("SEMRUSH_API_KEY")


def _parse(text: str) -> list[dict]:
    """Parse Semrush semicolon-separated response into list of dicts."""
    if text.startswith("ERROR"):
        return []
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if len(lines) < 2:
        return []
    headers = [h.strip() for h in lines[0].split(";")]
    rows = []
    for line in lines[1:]:
        vals = [v.strip() for v in line.split(";")]
        if len(vals) >= len(headers):
            rows.append(dict(zip(headers, vals)))
    return rows


def _clean_domain(domain: str) -> str:
    return (
        domain.replace("https://", "")
        .replace("http://", "")
        .replace("www.", "")
        .split("/")[0]
        .strip()
    )


# ─── Tool 1: Related Keywords (national) ────────────────────────────────────

class RelatedKeywordsInput(BaseModel):
    phrase: str = Field(description="Main niche term to find related keywords for (e.g. 'concrete')")
    limit: int = Field(default=30, description="Max results to return")


class SemrushRelatedKeywordsTool(BaseTool):
    name: str = "Semrush Related Keywords"
    description: str = (
        "Find related keywords for a niche term with national search volumes and CPCs. "
        "Use this to build the raw keyword list before narrowing to core keywords."
    )
    args_schema: Type[BaseModel] = RelatedKeywordsInput

    def _run(self, phrase: str, limit: int = 30) -> str:
        params = {
            "type": "phrase_related",
            "key": _api_key(),
            "phrase": phrase,
            "database": "us",
            "display_limit": limit,
            "export_columns": "Ph,Nq,Cp",
            "display_sort": "nq_desc",
        }
        try:
            resp = requests.get(SEMRUSH_BASE, params=params, timeout=20)
            rows = _parse(resp.text)
            if not rows:
                return f"No related keywords found for '{phrase}'"
            lines = [f"{'Keyword':<45} {'Volume':>12} {'CPC':>8}", "-" * 67]
            for r in rows[:25]:
                kw = r.get("Keyword", "?")
                vol = r.get("Search Volume", "0")
                cpc = r.get("CPC", "0")
                lines.append(f"{kw:<45} {vol:>12} ${cpc:>7}")
            return "\n".join(lines)
        except Exception as e:
            return f"Semrush error: {e}"


# ─── Tool 2: Single keyword lookup ──────────────────────────────────────────

class KeywordInput(BaseModel):
    phrase: str = Field(description="The keyword phrase to look up (e.g. 'concrete contractors')")


class SemrushKeywordTool(BaseTool):
    name: str = "Semrush Keyword Lookup"
    description: str = "Get search volume and CPC for a specific keyword phrase nationally."
    args_schema: Type[BaseModel] = KeywordInput

    def _run(self, phrase: str) -> str:
        params = {
            "type": "phrase_this",
            "key": _api_key(),
            "phrase": phrase,
            "database": "us",
            "export_columns": "Ph,Nq,Cp,Co",
        }
        try:
            resp = requests.get(SEMRUSH_BASE, params=params, timeout=20)
            rows = _parse(resp.text)
            if not rows:
                return f"No data for '{phrase}'"
            r = rows[0]
            return (
                f"Keyword: {r.get('Keyword', phrase)}\n"
                f"Monthly Volume: {r.get('Search Volume', '0')}\n"
                f"CPC: ${r.get('CPC', '0')}\n"
                f"Competition: {r.get('Competition', '?')}"
            )
        except Exception as e:
            return f"Semrush error: {e}"


# ─── Tool 3: City keyword check ──────────────────────────────────────────────

class CityKeywordInput(BaseModel):
    keyword: str = Field(description="The niche keyword (e.g. 'concrete contractors')")
    city: str = Field(description="City name (e.g. 'Ocala')")
    state: str = Field(description="State abbreviation (e.g. 'FL')")


class SemrushCityKeywordTool(BaseTool):
    name: str = "Semrush City Keyword Check"
    description: str = (
        "Check search volume and CPC for a keyword in a specific city. "
        "Searches '[keyword] [city] [state]' to evaluate local demand. "
        "Returns PASS or FAIL with exact thresholds: volume 30+, CPC $0.01-$4.99."
    )
    args_schema: Type[BaseModel] = CityKeywordInput

    def _run(self, keyword: str, city: str, state: str) -> str:
        phrases_to_try = [
            f"{keyword} {city} {state}",
            f"{keyword} {city}",
        ]
        for phrase in phrases_to_try:
            params = {
                "type": "phrase_this",
                "key": _api_key(),
                "phrase": phrase,
                "database": "us",
                "export_columns": "Ph,Nq,Cp",
            }
            try:
                resp = requests.get(SEMRUSH_BASE, params=params, timeout=20)
                rows = _parse(resp.text)
                if rows:
                    r = rows[0]
                    try:
                        vol = int(r.get("Search Volume", "0") or 0)
                    except ValueError:
                        vol = 0
                    try:
                        cpc = float(r.get("CPC", "0") or 0)
                    except ValueError:
                        cpc = 0.0

                    if vol < 30:
                        status = f"FAIL — volume too low ({vol} < 30 minimum)"
                    elif cpc == 0.0:
                        status = "FAIL — $0 CPC means no commercial value, nobody is bidding"
                    elif cpc >= 5.0:
                        status = f"FAIL — CPC ${cpc:.2f} too high (max $4.99)"
                    else:
                        status = "PASS ✅"

                    return (
                        f"City: {city}, {state}\n"
                        f"Keyword checked: {r.get('Keyword', phrase)}\n"
                        f"Monthly Volume: {vol}\n"
                        f"CPC: ${cpc:.2f}\n"
                        f"Result: {status}"
                    )
            except Exception as e:
                continue

        return (
            f"City: {city}, {state}\n"
            f"Keyword: {keyword}\n"
            f"Monthly Volume: 0\n"
            f"CPC: $0.00\n"
            f"Result: FAIL — no Semrush data found (volume too low or city too small)"
        )


# ─── Tool 4: Domain overview ─────────────────────────────────────────────────

class DomainInput(BaseModel):
    domain: str = Field(description="Competitor domain (e.g. 'ssconcreteaz.com')")


class SemrushDomainTool(BaseTool):
    name: str = "Semrush Domain Analysis"
    description: str = (
        "Get SEO authority and organic traffic data for a competitor domain. "
        "If ERROR 50 is returned, the domain has NO Semrush presence — green flag."
    )
    args_schema: Type[BaseModel] = DomainInput

    def _run(self, domain: str) -> str:
        domain = _clean_domain(domain)
        params = {
            "type": "domain_ranks",
            "key": _api_key(),
            "domain": domain,
            "database": "us",
            "export_columns": "Dn,Rk,Or,Ot,Oc,Ad,At,Ac",
        }
        try:
            resp = requests.get(SEMRUSH_BASE, params=params, timeout=20)
            if "ERROR 50" in resp.text or not resp.text.strip():
                return (
                    f"Domain: {domain}\n"
                    f"Semrush Data: NOT FOUND — domain has zero/near-zero organic presence\n"
                    f"Organic Keywords: 0\n"
                    f"Monthly Traffic: 0\n"
                    f"Assessment: GREEN FLAG ✅ — not ranking for anything"
                )
            rows = _parse(resp.text)
            if not rows:
                return (
                    f"Domain: {domain}\n"
                    f"Semrush Data: No data — minimal online presence\n"
                    f"Assessment: GREEN FLAG ✅"
                )
            r = rows[0]
            organic_kw = r.get("Organic Keywords", "0")
            organic_traffic = r.get("Organic Traffic", "0")
            try:
                ok_int = int(organic_kw)
                if ok_int == 0:
                    seo_strength = "WEAK ✅ (not ranking)"
                elif ok_int < 100:
                    seo_strength = "MODERATE ⚠️"
                else:
                    seo_strength = "STRONG 🚫"
            except ValueError:
                seo_strength = "UNKNOWN"
            return (
                f"Domain: {domain}\n"
                f"Semrush Rank: {r.get('Rank', 'N/A')}\n"
                f"Organic Keywords: {organic_kw} — {seo_strength}\n"
                f"Est. Monthly Traffic: {organic_traffic}\n"
                f"Paid Keywords: {r.get('Adwords Keywords', '0')}"
            )
        except Exception as e:
            return f"Error analyzing {domain}: {e}"


# ─── Tool 5: Backlinks ───────────────────────────────────────────────────────

class SemrushBacklinksTool(BaseTool):
    name: str = "Semrush Backlinks"
    description: str = (
        "Get backlink count for a competitor domain. "
        "0-10 backlinks = very weak (green flag). 98+ = red flag. "
        "ERROR 50 or no data = zero backlinks = GREEN FLAG."
    )
    args_schema: Type[BaseModel] = DomainInput

    def _run(self, domain: str) -> str:
        domain = _clean_domain(domain)
        params = {
            "key": _api_key(),
            "type": "backlinks_overview",
            "target": domain,
            "target_type": "root_domain",
            "export_columns": "total,domains_num,follows_num,nofollows_num",
        }
        try:
            resp = requests.get(SEMRUSH_ANALYTICS, params=params, timeout=20)
            if "ERROR 50" in resp.text or not resp.text.strip():
                return (
                    f"Domain: {domain}\n"
                    f"Total Backlinks: 0 — VERY WEAK ✅ (Green Flag)\n"
                    f"Referring Domains: 0\n"
                    f"Assessment: No backlink profile found — extremely easy to outrank"
                )
            rows = _parse(resp.text)
            if not rows:
                return f"Domain: {domain}\nTotal Backlinks: 0 — VERY WEAK ✅ (Green Flag)"
            r = rows[0]
            try:
                total = int(r.get("total", "0") or 0)
            except ValueError:
                total = 0
            try:
                domains = int(r.get("domains_num", "0") or 0)
            except ValueError:
                domains = 0

            if total <= 10:
                strength = "VERY WEAK ✅ (easy to beat)"
            elif total <= 50:
                strength = "MODERATE ⚠️"
            elif total <= 97:
                strength = "HEAVY ⚠️"
            else:
                strength = "VERY HEAVY 🚫 (red flag)"

            return (
                f"Domain: {domain}\n"
                f"Total Backlinks: {total} — {strength}\n"
                f"Referring Domains: {domains}\n"
                f"DoFollow: {r.get('follows_num', '0')} | NoFollow: {r.get('nofollows_num', '0')}"
            )
        except Exception as e:
            return f"Error fetching backlinks for {domain}: {e}"
