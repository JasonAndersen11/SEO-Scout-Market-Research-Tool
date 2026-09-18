import re
import threading
from crewai import Crew, Process

from .agents import (
    keyword_researcher,
    city_scout,
    competitor_identifier,
    market_analyst,
    prospect_builder,
    ad_copywriter,
)
from .tasks import (
    keyword_research_task,
    city_selection_task,
    competitor_identification_task,
    market_analysis_task,
    prospect_building_task,
    ad_copy_task,
)
from .tools.ahrefs import (
    AhrefsRelatedKeywordsTool,
    AhrefsKeywordTool,
    AhrefsCityKeywordTool,
    AhrefsDomainTool,
    AhrefsBacklinksTool,
)
from .tools.serper_search import SerperLocationSearchTool, SerperMapsSearchTool, SerperAdsSearchTool
from .tools.domain_analyzer import DomainAgeTool, WebsiteContentTool
from .keyword_cache import KEYWORD_CACHE


class StoppedError(Exception):
    pass


class RankRentPipeline:
    def __init__(self, niche: str, state: str, city: str = None, stop_event: threading.Event = None, resume_state: dict = None, update_callback=None):
        self.niche = niche.strip().lower()
        self.state = state.strip().upper()
        self.city = city.strip() if city else None
        self.stop_event = stop_event
        self.resume_state = resume_state or {}
        self.cb = update_callback or (lambda phase, status, data: None)

        # Instantiate all tools once
        self.t_related = AhrefsRelatedKeywordsTool()
        self.t_keyword = AhrefsKeywordTool()
        self.t_city = AhrefsCityKeywordTool()
        self.t_domain = AhrefsDomainTool()
        self.t_backlinks = AhrefsBacklinksTool()
        self.t_maps = SerperMapsSearchTool()
        self.t_ads = SerperAdsSearchTool()
        self.t_search = SerperLocationSearchTool()
        self.t_age = DomainAgeTool()
        self.t_content = WebsiteContentTool()

    def _check_stop(self):
        if self.stop_event and self.stop_event.is_set():
            raise StoppedError("Research stopped by user.")

    def _emit(self, phase: str, status: str, data: str):
        self.cb(phase, status, data)

    def _run(self, agents, tasks):
        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=False,
        )
        return str(crew.kickoff())

    def run(self) -> dict:
        r = self.resume_state
        results = {}

        # ── Phase 1: Keyword Research ──────────────────────────────────────
        if "keywords" in r:
            kw_output = r["keywords"]
            results["keywords"] = kw_output
            self._emit("keywords", "complete", kw_output)
        elif self.niche in KEYWORD_CACHE:
            self._emit("keywords", "running", f"Loading cached keywords for {self.niche}...")
            kw_output = KEYWORD_CACHE[self.niche]
            results["keywords"] = kw_output
            self._emit("keywords", "complete", kw_output)
        else:
            self._emit("keywords", "running", f"Researching keywords for {self.niche}...")
            kw_agent = keyword_researcher([self.t_related, self.t_keyword])
            kw_task = keyword_research_task(kw_agent, self.niche)
            kw_output = self._run([kw_agent], [kw_task])
            results["keywords"] = kw_output
            self._emit("keywords", "complete", kw_output)

        self._check_stop()

        # ── Phase 2: City Selection ────────────────────────────────────────
        if "cities" in r:
            city_output = r["cities"]
            results["cities"] = city_output
            self._emit("cities", "complete", city_output)
            qualifying_cities = [self.city] if self.city else self._extract_all_cities(city_output)
        elif self.city:
            city_output = f"User specified city: {self.city}, {self.state}\nProceeding directly to competitor research."
            self._emit("cities", "complete", city_output)
            qualifying_cities = [self.city]
        else:
            self._emit("cities", "running", f"Finding qualifying cities in {self.state}...")
            cs_agent = city_scout([self.t_city])
            cs_task = city_selection_task(cs_agent, self.state, kw_output)
            city_output = self._run([cs_agent], [cs_task])
            results["cities"] = city_output
            self._emit("cities", "complete", city_output)
            qualifying_cities = self._extract_all_cities(city_output)

        # ── No qualifying cities — stop the pipeline here ─────────────────
        if not qualifying_cities:
            msg = (
                f"No qualifying cities found in {self.state} — "
                "all cities failed on CPC ($0 or $5+) or volume (<30). "
                "Try a different state."
            )
            self._emit("competitors", "skipped", msg)
            self._emit("analysis", "skipped", msg)
            self._emit("prospects", "skipped", msg)
            self._emit("adcopy", "skipped", msg)
            results["no_cities"] = True
            return results

        self._check_stop()

        # ── Phases 3 & 4: Loop through qualifying cities until GO ─────────
        is_go = False
        target_city = qualifying_cities[0]
        comp_output = ""
        analysis_output = ""

        for idx, attempt_city in enumerate(qualifying_cities):
            self._check_stop()

            city_label = f"{attempt_city}, {self.state}"
            total = len(qualifying_cities)

            # Phase 3: Competitor Identification
            if "competitors" in r and idx == 0:
                comp_output = r["competitors"]
                results["competitors"] = comp_output
                self._emit("competitors", "complete", comp_output)
            else:
                msg = f"Searching competitors in {city_label}..."
                if total > 1:
                    msg += f" (city {idx + 1} of {total})"
                self._emit("competitors", "running", msg)
                ci_agent = competitor_identifier([self.t_maps, self.t_ads])
                ci_task = competitor_identification_task(ci_agent, self.niche, attempt_city, self.state, kw_output)
                comp_output = self._run([ci_agent], [ci_task])
                results["competitors"] = comp_output
                self._emit("competitors", "complete", comp_output)

            self._check_stop()

            # Phase 4: Market Analysis
            if "analysis" in r and idx == 0:
                analysis_output = r["analysis"]
                results["analysis"] = analysis_output
                self._emit("analysis", "complete", analysis_output)
            else:
                self._emit("analysis", "running", f"Scoring market in {city_label}...")
                ma_agent = market_analyst([self.t_domain, self.t_backlinks, self.t_age, self.t_content, self.t_search])
                ma_task = market_analysis_task(ma_agent, self.niche, attempt_city, self.state, comp_output)
                analysis_output = self._run([ma_agent], [ma_task])
                results["analysis"] = analysis_output
                self._emit("analysis", "complete", analysis_output)

            is_go = self._is_go(analysis_output)
            if is_go:
                target_city = attempt_city
                break

            # NO-GO — try next city if available
            next_idx = idx + 1
            if next_idx < len(qualifying_cities):
                next_city = qualifying_cities[next_idx]
                self._emit(
                    "analysis", "complete",
                    analysis_output + f"\n\n⚠️ NO-GO for {city_label} — automatically moving to next qualifying city: {next_city}, {self.state}"
                )
            else:
                self._emit(
                    "analysis", "complete",
                    analysis_output + f"\n\n🚫 NO-GO for all qualifying cities in {self.state}. Try a different state."
                )

        self._check_stop()

        if not is_go:
            no_go_msg = (
                f"🚫 NO-GO for all qualifying cities in {self.state}. "
                "None passed the Phase 4 due diligence scorecard. "
                "Try a different state or niche."
            )
            self._emit("prospects", "skipped", no_go_msg)
            self._emit("adcopy", "skipped", no_go_msg)
            results["no_cities"] = True
            return results

        if is_go:
            results["target_city"] = target_city

            # ── Phase 5: Prospect List ─────────────────────────────────────
            if "prospects" in r:
                prospect_output = r["prospects"]
                results["prospects"] = prospect_output
                self._emit("prospects", "complete", prospect_output)
            else:
                self._emit("prospects", "running", f"Building prospect list for {target_city}, {self.state}...")
                pb_agent = prospect_builder([self.t_ads, self.t_maps, self.t_content])
                pb_task = prospect_building_task(pb_agent, self.niche, target_city, self.state, kw_output)
                prospect_output = self._run([pb_agent], [pb_task])
                results["prospects"] = prospect_output
                self._emit("prospects", "complete", prospect_output)

            self._check_stop()

            # ── Phase 6: Ad Copy ──────────────────────────────────────────
            if "adcopy" in r:
                adcopy_output = r["adcopy"]
                results["adcopy"] = adcopy_output
                self._emit("adcopy", "complete", adcopy_output)
            else:
                self._emit("adcopy", "running", f"Writing Google + Facebook ad copy for {target_city}...")
                ac_agent = ad_copywriter()
                ac_task = ad_copy_task(ac_agent, self.niche, target_city, self.state, kw_output)
                adcopy_output = self._run([ac_agent], [ac_task])
                results["adcopy"] = adcopy_output
                self._emit("adcopy", "complete", adcopy_output)

        results["niche"] = self.niche
        results["state"] = self.state
        return results

    def _extract_all_cities(self, city_output: str) -> list:
        import re as _re

        # Hard bail only if the agent explicitly said nothing qualified
        text_upper = city_output.upper()
        hard_fail_signals = [
            "NO QUALIFYING CITIES FOUND",
            "NO CITIES QUALIFY",
            "NONE QUALIFY",
            "NO MARKETS QUALIFY",
            "0 QUALIFYING",
            "ZERO QUALIFYING",
        ]
        if any(s in text_upper for s in hard_fail_signals):
            # Only bail if there are also no PASS lines in the output
            if "PASS" not in text_upper:
                return []

        # Only scan the section before REJECTED CITIES so we don't pick up
        # city names from the failed list
        qualifying_section = city_output
        for marker in ("REJECTED CITIES", "REJECTED:"):
            if marker in city_output.upper():
                idx = city_output.upper().index(marker)
                qualifying_section = city_output[:idx]
                break

        cities = []

        # Match "1. City Name, ST" numbered list entries
        for match in _re.finditer(r'^\s*\d+\.\s*([A-Za-z][a-zA-Z ]+),\s*[A-Z]{2}', qualifying_section, _re.MULTILINE):
            city = match.group(1).strip().title()
            if city not in cities:
                cities.append(city)

        # Also catch lines like "City, ST — RECOMMENDED" or "City, ST  PASS"
        for match in _re.finditer(r'([A-Za-z][a-zA-Z ]+),\s*[A-Z]{2}[^\n]*(?:PASS|RECOMMENDED)', qualifying_section, _re.IGNORECASE):
            city = match.group(1).strip().title()
            if city not in cities:
                cities.append(city)

        # Put the RECOMMENDED city first
        # Pattern handles both "RECOMMENDATION: Ocala, FL" and "RECOMMENDATION: Proceed with Ocala, FL"
        rec = _re.search(r'(?:RECOMMENDATION[:\s]+(?:Proceed with\s+)?|Proceed with\s+)([A-Za-z][a-zA-Z ]+),\s*[A-Z]{2}', city_output, _re.IGNORECASE)
        if rec:
            rec_city = rec.group(1).strip().title()
            if rec_city in cities:
                cities.remove(rec_city)
            cities.insert(0, rec_city)

        # Fallback to single-city extractor
        if not cities:
            single = self._extract_city(city_output)
            if single != "Unknown City":
                cities = [single]

        return cities

    def _no_qualifying_cities(self, city_output: str, target_city: str) -> bool:
        if target_city != "Unknown City":
            return False
        text = city_output.upper()
        signals = [
            "NO QUALIFYING CITIES",
            "NO CITIES QUALIFY",
            "NONE QUALIFY",
            "NO MARKETS QUALIFY",
            "NO QUALIFYING MARKETS",
            "0 QUALIFYING",
            "ZERO QUALIFYING",
        ]
        return any(s in text for s in signals) or target_city == "Unknown City"

    def _is_go(self, text: str) -> bool:
        for line in text.split("\n"):
            u = line.upper().strip()
            if not ("VERDICT" in u or "MARKET" in u):
                continue
            if "NO-GO" in u or "NO GO" in u:
                return False
            if "GO" in u:
                return True
        # Fallback: green flags outnumber red flags 2:1
        return text.count("✅") >= text.count("🚫") * 2

    def _extract_city(self, city_output: str) -> str:
        import re as _re
        patterns = [
            r"(?:Proceed with|RECOMMENDATION[:\s]+)\s*([A-Za-z][a-zA-Z ]+),\s*[A-Z]{2}",
            r"^\s*\d+\.\s*([A-Za-z][a-zA-Z ]+),\s*[A-Z]{2}.*RECOMMEND",
            r"([A-Za-z][a-zA-Z ]+),\s*[A-Z]{2}.*PASS\s*✅",
            r"([A-Za-z][a-zA-Z ]+),\s*(?:FL|TX|AZ|NV|TN|SC|UT)\b",
        ]
        for pattern in patterns:
            match = _re.search(pattern, city_output, _re.MULTILINE | _re.IGNORECASE)
            if match:
                return match.group(1).strip().title()
        return "Unknown City"
