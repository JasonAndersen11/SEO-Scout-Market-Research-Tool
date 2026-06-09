import re
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
from .tools.semrush import (
    SemrushRelatedKeywordsTool,
    SemrushKeywordTool,
    SemrushCityKeywordTool,
    SemrushDomainTool,
    SemrushBacklinksTool,
)
from .tools.serper_search import SerperLocationSearchTool, SerperMapsSearchTool, SerperAdsSearchTool
from .tools.domain_analyzer import DomainAgeTool, WebsiteContentTool
from .keyword_cache import KEYWORD_CACHE


class RankRentPipeline:
    def __init__(self, niche: str, state: str, city: str = None, update_callback=None):
        self.niche = niche.strip().lower()
        self.state = state.strip().upper()
        self.city = city.strip() if city else None
        self.cb = update_callback or (lambda phase, status, data: None)

        # Instantiate all tools once
        self.t_related = SemrushRelatedKeywordsTool()
        self.t_keyword = SemrushKeywordTool()
        self.t_city = SemrushCityKeywordTool()
        self.t_domain = SemrushDomainTool()
        self.t_backlinks = SemrushBacklinksTool()
        self.t_maps = SerperMapsSearchTool()
        self.t_ads = SerperAdsSearchTool()
        self.t_search = SerperLocationSearchTool()
        self.t_age = DomainAgeTool()
        self.t_content = WebsiteContentTool()

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
        results = {}

        # ── Phase 1: Keyword Research ──────────────────────────────────────
        if self.niche in KEYWORD_CACHE:
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

        # ── Phase 2: City Selection ────────────────────────────────────────
        if self.city:
            city_output = f"User specified city: {self.city}, {self.state}\nProceeding directly to competitor research."
            target_city = self.city
            self._emit("cities", "complete", city_output)
        else:
            self._emit("cities", "running", f"Finding qualifying cities in {self.state}...")
            cs_agent = city_scout([self.t_city])
            cs_task = city_selection_task(cs_agent, self.state, kw_output)
            city_output = self._run([cs_agent], [cs_task])
            results["cities"] = city_output
            self._emit("cities", "complete", city_output)
            target_city = self._extract_city(city_output)

        results["target_city"] = target_city

        # ── Phase 3: Competitor Identification ────────────────────────────
        self._emit("competitors", "running", f"Searching competitors in {target_city}, {self.state}...")
        ci_agent = competitor_identifier([self.t_maps, self.t_ads])
        ci_task = competitor_identification_task(ci_agent, self.niche, target_city, self.state, kw_output)
        comp_output = self._run([ci_agent], [ci_task])
        results["competitors"] = comp_output
        self._emit("competitors", "complete", comp_output)

        # ── Phase 4: Market Analysis + Verdict ───────────────────────────
        self._emit("analysis", "running", "Pulling domain data and scoring competitors...")
        ma_agent = market_analyst([self.t_domain, self.t_backlinks, self.t_age, self.t_content])
        ma_task = market_analysis_task(ma_agent, self.niche, target_city, self.state, comp_output)
        analysis_output = self._run([ma_agent], [ma_task])
        results["analysis"] = analysis_output
        self._emit("analysis", "complete", analysis_output)

        # Check verdict
        is_go = self._is_go(analysis_output)

        if is_go:
            # ── Phase 5: Prospect List ─────────────────────────────────────
            self._emit("prospects", "running", f"Building prospect list for {target_city}...")
            pb_agent = prospect_builder([self.t_ads, self.t_maps, self.t_content])
            pb_task = prospect_building_task(pb_agent, self.niche, target_city, self.state, kw_output)
            prospect_output = self._run([pb_agent], [pb_task])
            results["prospects"] = prospect_output
            self._emit("prospects", "complete", prospect_output)

            # ── Phase 7: Ad Copy ──────────────────────────────────────────
            self._emit("adcopy", "running", "Writing Google + Facebook ad copy...")
            ac_agent = ad_copywriter()
            ac_task = ad_copy_task(ac_agent, self.niche, target_city, self.state, kw_output)
            adcopy_output = self._run([ac_agent], [ac_task])
            results["adcopy"] = adcopy_output
            self._emit("adcopy", "complete", adcopy_output)
        else:
            self._emit(
                "prospects",
                "skipped",
                f"Market in {target_city} is NO-GO. Check qualifying cities above and try the next one.",
            )
            self._emit("adcopy", "skipped", "Ad copy skipped — market did not qualify.")

        results["niche"] = self.niche
        results["state"] = self.state
        return results

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
