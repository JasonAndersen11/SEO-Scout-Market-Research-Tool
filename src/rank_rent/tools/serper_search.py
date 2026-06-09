import os
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

SERPER_SEARCH_URL = "https://google.serper.dev/search"
SERPER_MAPS_URL = "https://google.serper.dev/maps"

AGGREGATORS = {
    "yelp", "homeadvisor", "angi", "angieslist", "bbb", "homedepot",
    "thumbtack", "porch", "bark", "networx", "fixr", "lowes",
    "amazon", "facebook", "instagram", "twitter", "linkedin",
}


def _api_key():
    return os.getenv("SERPER_API_KEY")


def _is_aggregator(url: str) -> bool:
    url_lower = url.lower()
    return any(agg in url_lower for agg in AGGREGATORS)


# ─── Tool 1: Maps 3-Pack Search (for competitor identification) ──────────────

class MapsSearchInput(BaseModel):
    query: str = Field(description="The search query (e.g. 'concrete contractors Gainesville FL')")
    location: str = Field(description="Full location string (e.g. 'Gainesville, Florida, United States')")


class SerperMapsSearchTool(BaseTool):
    name: str = "Google Maps Competitor Search"
    description: str = (
        "Search Google Maps from a specific city to find businesses in the Maps 3-pack. "
        "Returns business names, websites (or NO WEBSITE), ratings, and review counts. "
        "Use this to identify the top map competitors for a niche in a city. "
        "IGNORE aggregators: Yelp, HomeAdvisor, Angi, BBB, Home Depot."
    )
    args_schema: Type[BaseModel] = MapsSearchInput

    def _run(self, query: str, location: str) -> str:
        headers = {
            "X-API-KEY": _api_key(),
            "Content-Type": "application/json",
        }
        payload = {
            "q": query,
            "location": location,
            "gl": "us",
            "hl": "en",
        }
        try:
            resp = requests.post(SERPER_MAPS_URL, headers=headers, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            places = data.get("places", [])

            if not places:
                return f"Maps search '{query}' in {location}: No Maps results found"

            lines = [f"Maps results: '{query}' in {location}"]
            for i, p in enumerate(places[:5], 1):
                name = p.get("title", "Unknown")
                website = p.get("website", "NO WEBSITE")
                rating = p.get("rating", "?")
                reviews = p.get("ratingCount", "?")
                phone = p.get("phoneNumber", "")
                flag = " ⭐ MASSIVE GREEN FLAG — NO WEBSITE" if website == "NO WEBSITE" else ""
                lines.append(
                    f"{i}. {name} | Website: {website}{flag}\n"
                    f"   Rating: {rating} ({reviews} reviews)"
                    + (f" | Phone: {phone}" if phone else "")
                )
            return "\n".join(lines)

        except Exception as e:
            return f"Maps search error for '{query}': {e}"


# ─── Tool 2: Google Ads Search (for prospect identification) ─────────────────

class AdsSearchInput(BaseModel):
    query: str = Field(description="The search query to find businesses running Google Ads")
    location: str = Field(description="Full location string (e.g. 'Gainesville, Florida, United States')")


class SerperAdsSearchTool(BaseTool):
    name: str = "Google Ads Prospect Search"
    description: str = (
        "Search Google to find businesses currently running Google Ads for a niche in a city. "
        "Returns sponsored/ad results — these are priority prospects because they're actively spending. "
        "Also returns organic results from real contractor websites (not aggregators). "
        "NEVER count Yelp, HomeAdvisor, Angi, BBB as real businesses."
    )
    args_schema: Type[BaseModel] = AdsSearchInput

    def _run(self, query: str, location: str) -> str:
        headers = {
            "X-API-KEY": _api_key(),
            "Content-Type": "application/json",
        }
        payload = {
            "q": query,
            "location": location,
            "gl": "us",
            "hl": "en",
            "num": 10,
        }
        try:
            resp = requests.post(SERPER_SEARCH_URL, headers=headers, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            lines = [f"Ad search: '{query}' in {location}"]

            # Google Ads (priority prospects)
            ads = data.get("ads", [])
            real_ads = [a for a in ads if not _is_aggregator(a.get("link", ""))]
            if real_ads:
                lines.append("GOOGLE ADS (Active spenders — call these first):")
                for ad in real_ads[:6]:
                    title = ad.get("title", "").strip()
                    link = ad.get("link", "")
                    domain = ad.get("domain", link.split("/")[2] if "//" in link else link)
                    lines.append(f"  AD: {title} | {domain} | {link}")
            else:
                lines.append("GOOGLE ADS: None found for this keyword")

            # Real organic results (non-aggregator)
            organic = data.get("organic", [])
            real_organic = [r for r in organic if not _is_aggregator(r.get("link", ""))]
            if real_organic:
                lines.append("ORGANIC (real contractor sites):")
                for r in real_organic[:4]:
                    lines.append(f"  {r.get('title','')} | {r.get('link','')}")

            return "\n".join(lines)

        except Exception as e:
            return f"Ads search error for '{query}': {e}"


# ─── Tool 3: Combined search (backwards compat, used by prospect builder) ────

class LocationSearchInput(BaseModel):
    query: str = Field(description="The Google search query")
    location: str = Field(description="Full location string (e.g. 'Gainesville, Florida, United States')")


class SerperLocationSearchTool(BaseTool):
    name: str = "Google Location Search"
    description: str = (
        "Search Google from a specific location. Returns Google Ads, Maps 3-pack, and organic results. "
        "Use SerperMapsSearchTool for Maps-specific competitor research instead."
    )
    args_schema: Type[BaseModel] = LocationSearchInput

    def _run(self, query: str, location: str) -> str:
        maps_tool = SerperMapsSearchTool()
        ads_tool = SerperAdsSearchTool()

        maps_result = maps_tool._run(query, location)
        ads_result = ads_tool._run(query, location)

        return f"{ads_result}\n\n{maps_result}"
