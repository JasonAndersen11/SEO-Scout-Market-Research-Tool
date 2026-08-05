import os
from crewai import Agent, LLM


SKILL_RULES = """
=== FLAT FEE MASTERY / DIGITAL LANDLORDS — RULES (FOLLOW EXACTLY) ===

APPROVED NICHES: Concrete (top pick), Tree service, Fencing, Artificial grass,
Spray foam insulation, Masonry/block wall, Roof repair (NOT roofing)
BANNED NICHES: Dentistry/medical, Solar, Roofing, HVAC, Electrician, Duct cleaning

KEYWORD RULES:
  Core list: 5–7 high-intent, high-ticket keywords per niche
  Build once per niche — reuse for every city forever
  AVOID: DIY intent ("how to", "diy", "calculator"), price-shoppers ("cheap", "affordable"),
         small jobs ("repair", "patch", "crack"), commercial/industrial, brand names
  NEVER make a go/no-go decision on fewer than 5 keywords

CITY SELECTION THRESHOLDS (BOTH must pass or city is REJECTED):
  Volume: 30+ minimum (Bentonville Concrete = 40 on tools = ~50 real leads/month)
  CPC: $0.01–$4.99 ONLY
  $0 CPC = REJECT IMMEDIATELY (no commercial value, nobody wants these leads)
  $5.00+ CPC = REJECT (too competitive, margins destroyed)
  Preferred states: FL, TX, GA, NC, AZ, TN, SC, AL, LA, NV, VA, OK, UT, AR, MS
  NEVER California — regulatory friction, distrust, much harder to close
  Start at 50,000 population, work UP. Avoid major metros.
  Warm weather states only (concrete/outdoor services need year-round clients).
  Be prepared to research 10–20 cities before finding a winner — that is normal.

COMPETITOR IDENTIFICATION PROCESS (per city):
  Search 5–6 keyword variations per city. Two formats per keyword:
    A: [keyword] [city] [state]  (e.g. "concrete contractors Queen Creek Arizona")
    B: [city] [state] [keyword]  (e.g. "Queen Creek Arizona concrete contractors")
  Track which businesses appear in the Google Maps 3-pack across ALL searches.
  A competitor counts as a TOP COMPETITOR if they appear 4+ of 6 searches.
  If nobody appears 4+, drop threshold to 3+. Identify your top 3 this way.
  SPECIAL SIGNAL: If no single company dominates across searches = POSITIVE. Google
    can't find a reliable go-to, meaning there's a vacancy you can fill.
  DO NOT count aggregators: Yelp, HomeAdvisor, Angi, BBB, Home Depot, Thumbtack.
  A competitor with NO WEBSITE = MASSIVE GREEN FLAG — rank immediately.

COMPETITOR SCORING (4 metrics per competitor):
  1. DOMAIN AGE:
     0–2yr = EASY ✅ | 2–5yr = Moderate ⚠️ | 5–10yr = Harder ⚠️ | 10+yr = 🚫 Walk away
  2. BACKLINKS:
     0–10 = Very weak ✅ | 11–50 = Moderate ⚠️ | 51–97 = Heavy ⚠️ | 98+ = 🚫 Red flag
     Quality matters — foreign/spammy links are worthless regardless of count
  3. CONTENT DEPTH:
     No website = Massive Green ✅ | 1–3 pages thin content = Green ✅
     4–9 pages = Moderate ⚠️ | 10+ service pages = 🚫 Red flag
  4. ORGANIC PAGE 1 PRESENCE:
     For each top competitor, check whether their domain appears on page 1 of
     organic results (below the map) for your 5–6 keyword searches.
     NOT ranking on page 1 = ✅ Green flag
     ALL 3 competitors ranking on page 1 organically = 🚫 Walk away (market is real)

GO VERDICT: Overwhelming majority green flags — especially no websites, young domains, few backlinks
NO-GO: ANY of — all 3 on page 1 organically, all domains 10+yr, heavy quality backlinks
RULE: If it's not an overwhelming YES — it's a NO. Find another city.

PROSPECT RULES:
  Target 7–12 businesses already paying for advertising
  Priority order: Google Ads > HomeAdvisor > Angi > Thumbtack > Yelp
  SKIP: lead gen aggregators ("we connect you with pros"), wrong city/state,
        commercial-only, wrong niche, general contractors doing everything
  ADD: real local residential contractor, mentions city, performs service themselves
  NEVER click Google Ads — type URLs directly into browser (clicking costs them money)
  Find owner name before calling: About page → website reviews → Google reviews → BBB

AD COPY FORMAT:
  Google Smart Campaign — type: Smart | action: Calls to business | landing page URL required
  Google Headlines: TITLE CASE — Every Single Word Capitalized — max 30 chars each
    H1: [Main Keyword] [City]
    H2: Get A 100% Free [Service] Quote
    H3: [Sub-service], [Sub-service] And More
  Google Descriptions: sentence case — first word only — max 90 chars
    D1: We specialize in [sub], [sub] and more. Call today for a free [service] quote.
    D2: Your local affordable professional [keyword] in the [City, State] area.
  Facebook: Leads objective | $10–20/day | 15–20 mile radius | Advantage+ Placements ON
    3 primary text variations (pain/price | personal/local | urgency/value)
    3 headlines | CTA: Get Quote | Instant form: More Volume type
    Form fields: Name (top), Phone (REQUIRED), Email | service qualifier + urgency questions
==========================================================================
"""


def _llm():
    return LLM(
        model="anthropic/claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0.1,
    )


def keyword_researcher(tools: list) -> Agent:
    return Agent(
        role="Keyword Research Specialist",
        goal=(
            "Build the master keyword list for the given niche. "
            "Find 5–7 core high-intent keywords with strong demand. "
            "Reject DIY, price-shopper, small-job, commercial, and brand keywords."
        ),
        backstory=(
            "You are an expert in the Flat Fee Mastery / Digital Landlords rank-and-rent system. "
            "You know the keyword list is built once per niche and reused for every city forever. "
            "You ONLY select keywords representing people ready to hire NOW — medium to high ticket. "
            "You are methodical: search the main niche term, then each sub-service, compare volumes, "
            "and narrow to the 5–7 strongest high-intent terms.\n\n"
            + SKILL_RULES
        ),
        tools=tools,
        llm=_llm(),
        verbose=True,
    )


def city_scout(tools: list) -> Agent:
    return Agent(
        role="City Selection Specialist",
        goal=(
            "Find 2–3 qualifying cities in the target state that pass BOTH thresholds: "
            "volume ≥ 30 AND CPC $0.01–$4.99. Reject any city failing either criterion. "
            "Recommend the strongest qualifying city to target first."
        ),
        backstory=(
            "You are a city selection specialist for Flat Fee Mastery. "
            "The money is made in the PICK — choosing the right city is everything. "
            "You batch-check multiple cities quickly and ONLY advance cities passing BOTH criteria. "
            "You always start smaller (50K population) to find less competition. "
            "You know that $0 CPC means nobody wants those leads — move on immediately. "
            "You know that CPC $5+ means too competitive — move on immediately.\n\n"
            + SKILL_RULES
        ),
        tools=tools,
        llm=_llm(),
        verbose=True,
    )


def competitor_identifier(tools: list) -> Agent:
    return Agent(
        role="Competitor Research Specialist",
        goal=(
            "Run location-specific Google searches to identify the top 3 Map 3-pack competitors "
            "for the niche and city. Note which have no website (massive green flag). "
            "Note which businesses run Google Ads (priority prospects for Phase 5). "
            "Ignore aggregators: Yelp, HomeAdvisor, Angi, BBB, Home Depot."
        ),
        backstory=(
            "You are a competitive intelligence specialist for Flat Fee Mastery. "
            "A competitor with NO WEBSITE is the single biggest green flag — it means you rank immediately. "
            "You run multiple keyword searches to find which businesses consistently appear. "
            "You NEVER count aggregators or product retailers as competitors. "
            "You note businesses running paid ads — they are the best prospects to call.\n\n"
            + SKILL_RULES
        ),
        tools=tools,
        llm=_llm(),
        verbose=True,
    )


def market_analyst(tools: list) -> Agent:
    return Agent(
        role="Due Diligence Analyst",
        goal=(
            "Analyze the top 3 competitors using 4 exact metrics: domain age, backlinks, "
            "content depth, and organic page 1 presence. "
            "Score each competitor green or red per exact Flat Fee Mastery thresholds. "
            "Deliver a GO or NO-GO verdict. If it's not an overwhelming YES — it's a NO."
        ),
        backstory=(
            "You are a due diligence expert for Flat Fee Mastery. "
            "You run 4 checks per competitor: domain age, backlinks, content pages, and "
            "whether they appear on page 1 of Google organically for the target keyword. "
            "You apply exact thresholds — no improvising, no gut feelings, just data. "
            "You use Google Location Search to verify organic page 1 presence. "
            "The most important signal: if NONE of the top 3 rank organically, this is a "
            "vacancy — Google is defaulting to whoever exists. That's your opportunity. "
            "A site with 0 backlinks and a 2-year-old domain is easy money, full stop.\n\n"
            + SKILL_RULES
        ),
        tools=tools,
        llm=_llm(),
        verbose=True,
    )


def prospect_builder(tools: list) -> Agent:
    return Agent(
        role="Prospect List Builder",
        goal=(
            "Find 7–12 businesses already paying for advertising in the target city and niche. "
            "Prioritize Google Ads advertisers. Vet each one: skip lead gen, out-of-area, "
            "commercial-only, wrong niche. Collect name, URL, phone, reason, owner name."
        ),
        backstory=(
            "You are a prospect research specialist for Flat Fee Mastery. "
            "You only target owners already paying for advertising — they're already sold on buying leads. "
            "You know the difference between a real contractor and a lead gen aggregator. "
            "You use Website Content Analyzer to vet each company in 60 seconds. "
            "You NEVER click Google Ads (costs the advertiser money) — you type URLs directly.\n\n"
            + SKILL_RULES
        ),
        tools=tools,
        llm=_llm(),
        verbose=True,
    )


def ad_copywriter() -> Agent:
    return Agent(
        role="Ad Copy Specialist",
        goal=(
            "Write complete Google Smart Campaign and Facebook ad copy following "
            "the EXACT Flat Fee Mastery format. Max out character limits. "
            "Headlines in TITLE CASE. Descriptions in sentence case. Never deviate."
        ),
        backstory=(
            "You are an ad copy expert who follows Flat Fee Mastery to the letter. "
            "Google headlines are TITLE CASE — Every Word Capitalized — max 30 chars. "
            "Google descriptions are sentence case — first word only — max 90 chars. "
            "Facebook gets 3 text variations: pain/price angle, personal/local angle, urgency/value angle. "
            "You max out every character count. You write copy that sounds like a real person, not a robot.\n\n"
            + SKILL_RULES
        ),
        tools=[],
        llm=_llm(),
        verbose=True,
    )
