import requests
import whois
from datetime import datetime
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from bs4 import BeautifulSoup


def _clean_domain(domain: str) -> str:
    return domain.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0].strip()


# ─── Tool: Domain Age ────────────────────────────────────────────────────────

class DomainAgeInput(BaseModel):
    domain: str = Field(description="Domain to check age for (e.g. 'competitor.com')")


class DomainAgeTool(BaseTool):
    name: str = "Domain Age Checker"
    description: str = (
        "Check how old a domain is using WHOIS. "
        "0-2 years = EASY (green). 2-5 years = moderate. "
        "5-10 years = harder. 10+ years = red flag."
    )
    args_schema: Type[BaseModel] = DomainAgeInput

    def _run(self, domain: str) -> str:
        domain = _clean_domain(domain)
        try:
            w = whois.whois(domain)
            creation_date = w.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            if creation_date:
                if hasattr(creation_date, "year"):
                    age_years = (datetime.now() - creation_date).days / 365.25
                    created_str = creation_date.strftime("%Y-%m-%d")
                else:
                    return f"{domain}: Domain age data format unrecognized"

                if age_years < 2:
                    rating = "EASY ✅ (Green Flag)"
                elif age_years < 5:
                    rating = "MODERATE ⚠️"
                elif age_years < 10:
                    rating = "HARDER ⚠️"
                else:
                    rating = "VERY ESTABLISHED 🚫 (Red Flag)"

                return (
                    f"Domain: {domain}\n"
                    f"Created: {created_str}\n"
                    f"Age: {age_years:.1f} years\n"
                    f"Difficulty: {rating}"
                )
        except Exception:
            pass
        return (
            f"Domain: {domain}\n"
            f"Age: Could not determine (may be very new, private, or invalid)\n"
            f"Difficulty: Treat as UNKNOWN — check manually if critical"
        )


# ─── Tool: Website Content Analyzer ─────────────────────────────────────────

class WebsiteInput(BaseModel):
    url: str = Field(description="Competitor website URL to analyze for content depth")


class WebsiteContentTool(BaseTool):
    name: str = "Website Content Analyzer"
    description: str = (
        "Visit a competitor or prospect website to assess content depth and legitimacy. "
        "Checks: page count, homepage word count, service pages, is it a real local contractor "
        "or a lead gen aggregator. Thin content = green flag. 10+ pages = red flag."
    )
    args_schema: Type[BaseModel] = WebsiteInput

    def _run(self, url: str) -> str:
        if not url or url == "NO WEBSITE":
            return "NO WEBSITE — Massive Green Flag ✅ (competitor has no web presence)"
        if not url.startswith("http"):
            url = "https://" + url
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            resp = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, "lxml")

            # Check for lead gen signals
            text_lower = resp.text.lower()
            lead_gen_signals = [
                "connect you with", "matching you with", "get matched",
                "we connect homeowners", "find a pro", "find contractors near",
                "trusted network of", "vetted professionals"
            ]
            is_lead_gen = any(sig in text_lower for sig in lead_gen_signals)

            # Count internal links (proxy for page count)
            domain_part = url.split("/")[2]
            all_links = soup.find_all("a", href=True)
            internal = set()
            for a in all_links:
                href = a["href"]
                if href.startswith("/") and len(href) > 1:
                    internal.add(href)
                elif domain_part in href and href != url:
                    internal.add(href)
            page_count = len(internal)

            # Word count (excluding nav/footer/script)
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            words = len(soup.get_text(separator=" ", strip=True).split())

            # Service page detection
            nav_text = " ".join(
                a.get_text(strip=True).lower()
                for a in soup.find_all("a")
            )
            service_words = ["driveway", "patio", "staining", "stamped", "resurfacing",
                           "removal", "trimming", "grinding", "installation", "repair",
                           "insulation", "masonry", "retaining", "block wall"]
            service_pages_found = [w for w in service_words if w in nav_text]

            if is_lead_gen:
                content_score = "LEAD GEN AGGREGATOR 🚫 — Skip as prospect"
            elif page_count <= 3:
                content_score = "THIN ✅ (Green Flag — easy to beat)"
            elif page_count <= 8:
                content_score = "MODERATE ⚠️"
            else:
                content_score = "SUBSTANTIAL 🚫 (Red Flag — well-built site)"

            return (
                f"URL: {url}\n"
                f"Lead Gen Site: {'YES 🚫 — SKIP' if is_lead_gen else 'No — real contractor'}\n"
                f"Estimated Pages: {page_count}\n"
                f"Homepage Word Count: ~{words} words\n"
                f"Service Pages Found: {', '.join(service_pages_found) if service_pages_found else 'None detected'}\n"
                f"Content Assessment: {content_score}\n"
                f"Benchmark: If entering this market, write ~{words * 2} words on your homepage"
            )
        except Exception as e:
            return f"Could not analyze {url}: {e}\nTreat as: UNKNOWN — check manually"
