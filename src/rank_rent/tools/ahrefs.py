import os
from datetime import datetime, timezone
from typing import Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.rank_rent.city_cache import get as cache_get, put as cache_put

# Ahrefs API v3 — https://docs.ahrefs.com/api/docs/introduction.md
# Auth: Authorization: Bearer <AHREFS_API_KEY>
# CPC is returned in USD cents; volume is an estimated monthly search count.
AHREFS_BASE = "https://api.ahrefs.com/v3"
AHREFS_COUNTRY = "us"

# Keywords Explorer select columns (keep the set small to conserve API units).
KW_SELECT = "keyword,volume,cpc,difficulty"


def _api_key() -> str | None:
    return os.getenv("AHREFS_API_KEY")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Accept": "application/json",
    }


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _clean_domain(domain: str) -> str:
    return (
        domain.replace("https://", "")
        .replace("http://", "")
        .replace("www.", "")
        .split("/")[0]
        .strip()
    )


def cpc_to_dollars(cpc_cents) -> float:
    """Ahrefs CPC is in USD cents. None/invalid → 0.0."""
    if cpc_cents is None or cpc_cents == "":
        return 0.0
    try:
        return float(cpc_cents) / 100.0
    except (TypeError, ValueError):
        return 0.0


def volume_int(value) -> int:
    if value is None or value == "":
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0


def city_keyword_status(vol: int, cpc: float) -> str:
    """PASS/FAIL using Flat Fee Mastery thresholds (volume 30+, CPC $0.01–$4.99)."""
    if vol < 30:
        return f"FAIL — volume too low ({vol} < 30 minimum)"
    if cpc == 0.0:
        return "FAIL — $0 CPC means no commercial value, nobody is bidding"
    if cpc >= 5.0:
        return f"FAIL — CPC ${cpc:.2f} too high (max $4.99)"
    return "PASS ✅"


def backlink_strength(total: int) -> str:
    if total <= 10:
        return "VERY WEAK ✅ (easy to beat)"
    if total <= 50:
        return "MODERATE ⚠️"
    if total <= 97:
        return "HEAVY ⚠️"
    return "VERY HEAVY 🚫 (red flag)"


def organic_strength(organic_kw: int) -> str:
    if organic_kw == 0:
        return "WEAK ✅ (not ranking)"
    if organic_kw < 100:
        return "MODERATE ⚠️"
    return "STRONG 🚫"


def _missing_key_error() -> str:
    return (
        "Ahrefs error: AHREFS_API_KEY is not set. "
        "Create an API v3 key in Ahrefs → Account settings → API keys and add it to .env. "
        "See README for the SEMRUSH_API_KEY → AHREFS_API_KEY migration."
    )


def _error_message(status: int, data) -> str | None:
    if status == 401:
        return (
            "Ahrefs auth failed — check AHREFS_API_KEY "
            "(Bearer token from Account settings → API keys). "
            "MCP keys are not a substitute for API v3 keys."
        )
    if status == 403:
        return (
            "Ahrefs API forbidden — this key may lack API v3 access, "
            "or the workspace plan does not include these endpoints."
        )
    if status == 429:
        return "Ahrefs rate limited (HTTP 429). Default limit is 60 requests/minute."
    if status >= 400:
        err = data.get("error") if isinstance(data, dict) else str(data)
        return f"Ahrefs error ({status}): {err}"
    return None


def ahrefs_get(path: str, params: dict, timeout: int = 20) -> tuple[int, dict]:
    """GET https://api.ahrefs.com/v3{path}. Returns (status_code, json_dict)."""
    resp = requests.get(
        f"{AHREFS_BASE}{path}",
        headers=_headers(),
        params=params,
        timeout=timeout,
    )
    try:
        data = resp.json()
    except ValueError:
        data = {"error": (resp.text or "")[:500]}
    if not isinstance(data, dict):
        data = {"error": str(data)[:500]}
    return resp.status_code, data


# ─── Tool 1: Related Keywords (national) ────────────────────────────────────

class RelatedKeywordsInput(BaseModel):
    phrase: str = Field(description="Main niche term to find related keywords for (e.g. 'concrete')")
    limit: int = Field(default=30, description="Max results to return")


class AhrefsRelatedKeywordsTool(BaseTool):
    name: str = "Ahrefs Related Keywords"
    description: str = (
        "Find related keywords for a niche term with national search volumes and CPCs "
        "via Ahrefs Keywords Explorer matching terms. "
        "Use this to build the raw keyword list before narrowing to core keywords."
    )
    args_schema: Type[BaseModel] = RelatedKeywordsInput

    def _run(self, phrase: str, limit: int = 30) -> str:
        if not _api_key():
            return _missing_key_error()
        params = {
            "keywords": phrase,
            "country": AHREFS_COUNTRY,
            "select": KW_SELECT,
            "order_by": "volume:desc",
            "limit": max(1, min(int(limit or 30), 50)),
            "match_mode": "terms",
            "terms": "all",
        }
        try:
            status, data = ahrefs_get("/keywords-explorer/matching-terms", params)
            err = _error_message(status, data)
            if err:
                return err
            rows = data.get("keywords") or []
            if not rows:
                return f"No related keywords found for '{phrase}'"
            lines = [f"{'Keyword':<45} {'Volume':>12} {'CPC':>8}", "-" * 67]
            for r in rows[:25]:
                kw = r.get("keyword") or "?"
                vol = volume_int(r.get("volume"))
                cpc = cpc_to_dollars(r.get("cpc"))
                lines.append(f"{kw:<45} {vol:>12} ${cpc:>7.2f}")
            return "\n".join(lines)
        except Exception as e:
            return f"Ahrefs error: {e}"


# ─── Tool 2: Single keyword lookup ──────────────────────────────────────────

class KeywordInput(BaseModel):
    phrase: str = Field(description="The keyword phrase to look up (e.g. 'concrete contractors')")


class AhrefsKeywordTool(BaseTool):
    name: str = "Ahrefs Keyword Lookup"
    description: str = (
        "Get search volume, CPC, and keyword difficulty for a specific keyword phrase nationally "
        "via Ahrefs Keywords Explorer overview."
    )
    args_schema: Type[BaseModel] = KeywordInput

    def _run(self, phrase: str) -> str:
        if not _api_key():
            return _missing_key_error()
        params = {
            "keywords": phrase,
            "country": AHREFS_COUNTRY,
            "select": KW_SELECT,
            "limit": 1,
        }
        try:
            status, data = ahrefs_get("/keywords-explorer/overview", params)
            err = _error_message(status, data)
            if err:
                return err
            rows = data.get("keywords") or []
            if not rows:
                return f"No data for '{phrase}'"
            r = rows[0]
            cpc = cpc_to_dollars(r.get("cpc"))
            difficulty = r.get("difficulty")
            diff_str = "N/A" if difficulty is None else f"{difficulty}/100"
            return (
                f"Keyword: {r.get('keyword', phrase)}\n"
                f"Monthly Volume: {volume_int(r.get('volume'))}\n"
                f"CPC: ${cpc:.2f}\n"
                f"Keyword Difficulty: {diff_str}"
            )
        except Exception as e:
            return f"Ahrefs error: {e}"


# ─── Tool 3: City keyword check ──────────────────────────────────────────────

class CityKeywordInput(BaseModel):
    keyword: str = Field(description="The niche keyword (e.g. 'concrete contractors')")
    city: str = Field(description="City name (e.g. 'Ocala')")
    state: str = Field(description="State abbreviation (e.g. 'FL')")


class AhrefsCityKeywordTool(BaseTool):
    name: str = "Ahrefs City Keyword Check"
    description: str = (
        "Check search volume and CPC for a keyword in a specific city. "
        "Searches '[keyword] [city] [state]' to evaluate local demand. "
        "Returns PASS or FAIL with exact thresholds: volume 30+, CPC $0.01-$4.99."
    )
    args_schema: Type[BaseModel] = CityKeywordInput

    def _run(self, keyword: str, city: str, state: str) -> str:
        state = state.strip().upper()

        cached = cache_get(keyword, city, state)
        if cached:
            return cached + "\n[CACHED — no Ahrefs units used]"

        if not _api_key():
            return _missing_key_error()

        phrases_to_try = [
            f"{keyword} {city} {state}",
            f"{keyword} {city}",
        ]

        for phrase in phrases_to_try:
            params = {
                "keywords": phrase,
                "country": AHREFS_COUNTRY,
                "select": "keyword,volume,cpc",
                "limit": 1,
            }
            try:
                status, data = ahrefs_get("/keywords-explorer/overview", params)
                if status in (401, 403):
                    return _error_message(status, data) or f"Ahrefs error ({status})"
                if status >= 400:
                    continue
                rows = data.get("keywords") or []
                if not rows:
                    continue
                r = rows[0]
                vol = volume_int(r.get("volume"))
                cpc = cpc_to_dollars(r.get("cpc"))
                status_line = city_keyword_status(vol, cpc)
                result = (
                    f"City: {city}, {state}\n"
                    f"Keyword checked: {r.get('keyword', phrase)}\n"
                    f"Monthly Volume: {vol}\n"
                    f"CPC: ${cpc:.2f}\n"
                    f"Result: {status_line}"
                )
                cache_put(keyword, city, state, result)
                return result
            except Exception:
                continue

        # Ahrefs returned nothing (unknown keyword or exhausted API units).
        # Stub varied data so the pipeline can be tested end-to-end.
        # Remove this block and rerun once Ahrefs units are available.
        seed = sum(ord(c) for c in city)
        bucket = seed % 5

        if bucket == 0:
            vol, cpc = 18, 1.85
        elif bucket == 1:
            vol, cpc = 55, 6.20
        elif bucket == 2:
            vol, cpc = 40, 0.00
        elif bucket == 3:
            vol, cpc = 70, 3.10
        else:
            vol, cpc = 40, 1.45

        status_line = city_keyword_status(vol, cpc)
        return (
            f"City: {city}, {state}\n"
            f"Keyword: {keyword} {city} {state}\n"
            f"Monthly Volume: {vol} [STUB]\n"
            f"CPC: ${cpc:.2f} [STUB]\n"
            f"Result: {status_line} [STUB — rerun after restocking Ahrefs API units]"
        )


# ─── Tool 4: Domain overview ─────────────────────────────────────────────────

class DomainInput(BaseModel):
    domain: str = Field(description="Competitor domain (e.g. 'ssconcreteaz.com')")


class AhrefsDomainTool(BaseTool):
    name: str = "Ahrefs Domain Analysis"
    description: str = (
        "Get SEO authority and organic traffic data for a competitor domain from Ahrefs Site Explorer. "
        "Zero organic keywords / traffic = no Ahrefs presence — green flag."
    )
    args_schema: Type[BaseModel] = DomainInput

    def _run(self, domain: str) -> str:
        if not _api_key():
            return _missing_key_error()
        domain = _clean_domain(domain)
        params = {
            "target": domain,
            "date": _today(),
            "mode": "domain",
            "protocol": "both",
            "country": AHREFS_COUNTRY,
            "volume_mode": "average",
        }
        try:
            status, data = ahrefs_get("/site-explorer/metrics", params)
            err = _error_message(status, data)
            if err:
                return err
            metrics = data.get("metrics") or {}
            organic_kw = volume_int(metrics.get("org_keywords"))
            organic_traffic = volume_int(metrics.get("org_traffic"))
            paid_kw = volume_int(metrics.get("paid_keywords"))

            if organic_kw == 0 and organic_traffic == 0:
                return (
                    f"Domain: {domain}\n"
                    f"Ahrefs Data: NOT FOUND — domain has zero/near-zero organic presence\n"
                    f"Organic Keywords: 0\n"
                    f"Monthly Traffic: 0\n"
                    f"Assessment: GREEN FLAG ✅ — not ranking for anything"
                )

            dr_line = ""
            try:
                dr_status, dr_data = ahrefs_get(
                    "/site-explorer/domain-rating",
                    {
                        "target": domain,
                        "date": _today(),
                        "protocol": "both",
                    },
                )
                if dr_status == 200:
                    dr = (dr_data.get("domain_rating") or {})
                    rating = dr.get("domain_rating")
                    rank = dr.get("ahrefs_rank")
                    if rating is not None or rank is not None:
                        dr_line = (
                            f"Domain Rating: {rating if rating is not None else 'N/A'}  |  "
                            f"Ahrefs Rank: {rank if rank is not None else 'N/A'}\n"
                        )
            except Exception:
                dr_line = ""

            return (
                f"Domain: {domain}\n"
                f"{dr_line}"
                f"Organic Keywords: {organic_kw} — {organic_strength(organic_kw)}\n"
                f"Est. Monthly Traffic: {organic_traffic}\n"
                f"Paid Keywords: {paid_kw}"
            )
        except Exception as e:
            return f"Error analyzing {domain}: {e}"


# ─── Tool 5: Backlinks ───────────────────────────────────────────────────────

class AhrefsBacklinksTool(BaseTool):
    name: str = "Ahrefs Backlinks"
    description: str = (
        "Get live backlink count for a competitor domain from Ahrefs Site Explorer. "
        "0-10 backlinks = very weak (green flag). 98+ = red flag. "
        "No data / zero live backlinks = GREEN FLAG."
    )
    args_schema: Type[BaseModel] = DomainInput

    def _run(self, domain: str) -> str:
        if not _api_key():
            return _missing_key_error()
        domain = _clean_domain(domain)
        params = {
            "target": domain,
            "date": _today(),
            "mode": "domain",
            "protocol": "both",
        }
        try:
            status, data = ahrefs_get("/site-explorer/backlinks-stats", params)
            err = _error_message(status, data)
            if err:
                return err
            metrics = data.get("metrics") or {}
            total = volume_int(metrics.get("live"))
            domains = volume_int(metrics.get("live_refdomains"))

            if total == 0:
                return (
                    f"Domain: {domain}\n"
                    f"Total Backlinks: 0 — VERY WEAK ✅ (Green Flag)\n"
                    f"Referring Domains: 0\n"
                    f"Assessment: No backlink profile found — extremely easy to outrank"
                )

            return (
                f"Domain: {domain}\n"
                f"Total Backlinks: {total} — {backlink_strength(total)}\n"
                f"Referring Domains: {domains}\n"
                f"Live backlinks (Ahrefs). DoFollow/NoFollow split is not returned by backlinks-stats."
            )
        except Exception as e:
            return f"Error fetching backlinks for {domain}: {e}"
