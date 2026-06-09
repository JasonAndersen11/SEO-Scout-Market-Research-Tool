from crewai import Task


def keyword_research_task(agent, niche: str) -> Task:
    sub_services = {
        "concrete": "driveway, patio, stamped concrete, concrete staining, concrete resurfacing, concrete coating, polished concrete",
        "tree service": "tree removal, tree trimming, stump grinding, emergency tree removal, tree pruning",
        "artificial grass": "artificial turf installation, synthetic grass, fake grass, turf installation",
        "spray foam insulation": "spray foam insulation, open cell foam, closed cell foam, attic insulation",
        "masonry": "block wall, retaining wall, brick laying, stone masonry, concrete block wall",
        "roof repair": "roof repair, roof leak repair, shingle repair, roof patch, flat roof repair",
    }
    subs = sub_services.get(niche.lower(), f"{niche} contractor, {niche} company, {niche} installation")

    return Task(
        description=f"""
Build the master keyword list for the '{niche}' niche. Follow Flat Fee Mastery rules exactly.

STEP 1 — Use Semrush Related Keywords tool to search '{niche}' nationally. Get top keywords by volume.

STEP 2 — Also search each sub-service separately using Semrush Related Keywords:
Sub-services for {niche}: {subs}
Search each one individually to get their volumes and CPCs.

STEP 3 — Use Semrush Keyword Lookup to verify volume + CPC for the best candidates.

STEP 4 — Narrow to 5–7 CORE keywords (highest volume, highest intent, people ready to hire NOW).

REJECT from core list:
- DIY: "how to pour", "diy", "calculator", "how to"
- Price shoppers: "cheap", "affordable", "discount", "low cost"
- Small jobs: "crack repair", "patch", "small"
- Commercial: "commercial", "industrial"
- Brand: specific company names

GOOD core keyword examples for {niche}: contractor, company, {subs.split(',')[0]}, {subs.split(',')[1] if ',' in subs else ''}

Output format (use this exact structure):
---
NICHE: {niche.upper()}

CORE KEYWORDS (5–7):
1. [keyword] | Volume: [X]/mo | CPC: $[X]
2. [keyword] | Volume: [X]/mo | CPC: $[X]
3. [keyword] | Volume: [X]/mo | CPC: $[X]
4. [keyword] | Volume: [X]/mo | CPC: $[X]
5. [keyword] | Volume: [X]/mo | CPC: $[X]

RAW LIST (all researched):
[All keywords found with their volumes and CPCs]

PRIMARY KEYWORD (strongest for city checks): [keyword]
---
""",
        expected_output=(
            "A structured keyword list: 5–7 core high-intent keywords with volume and CPC, "
            "plus the full raw list and the primary keyword for city checks."
        ),
        agent=agent,
    )


def city_selection_task(agent, state: str, keyword_output: str) -> Task:
    city_suggestions = {
        "FL": "Ocala, Lakeland, Daytona Beach, Cape Coral, Gainesville, Pensacola, Tallahassee, Port St. Lucie, Deltona, Palm Bay, Kissimmee, Doral, Sanford, Leesburg",
        "TX": "Lubbock, Laredo, Amarillo, Waco, Midland, Odessa, Round Rock, Lewisville, Killeen, Beaumont, Allen, Frisco, McKinney, Carrollton, Pearland",
        "AZ": "Gilbert, Chandler, Glendale, Tempe, Surprise, Avondale, Peoria, Goodyear, Yuma, Flagstaff, Prescott, Casa Grande, Maricopa, Queen Creek, Buckeye",
        "NV": "Henderson, Reno, Sparks, North Las Vegas, Carson City, Enterprise, Spring Valley, Sunrise Manor",
        "TN": "Murfreesboro, Knoxville, Chattanooga, Clarksville, Jackson, Franklin, Smyrna, Hendersonville, Brentwood",
        "SC": "Columbia, Greenville, Spartanburg, Rock Hill, Mount Pleasant, Summerville, Goose Creek, Myrtle Beach, Florence",
        "UT": "Provo, Ogden, St. George, Orem, West Jordan, West Valley City, Sandy, South Jordan, Lehi, Draper",
    }
    suggestions = city_suggestions.get(state.upper(), f"major cities in {state} with 50,000–250,000 population")

    return Task(
        description=f"""
Find 2–3 qualifying cities in {state} for the rank-and-rent opportunity.

Keyword research from previous phase:
{keyword_output}

CRITERIA — BOTH must pass or city is REJECTED:
  Volume: 30+ minimum
  CPC: $0.01–$4.99 only
  $0 CPC = REJECT IMMEDIATELY
  $5.00+ CPC = REJECT IMMEDIATELY

CITIES TO CHECK in {state} (start here, check at least 10):
{suggestions}

AVOID: Major metros (Orlando, Tampa, Miami, Dallas, Phoenix, Las Vegas, Nashville, Houston)
PREFER: Cities 50,000–250,000 population

PROCESS:
1. Take the PRIMARY KEYWORD from the keyword output above
2. For each city, use Semrush City Keyword Check: "[primary keyword] [City] [State]"
3. Record result for each city (Volume, CPC, PASS/FAIL)
4. Check at least 10 cities before selecting finalists
5. Select 2–3 that pass BOTH criteria
6. Recommend the strongest one (best volume in the $0.01–$4.99 CPC range)

Output format:
---
CITY RESEARCH — {state.upper()}

QUALIFYING CITIES:
1. [City], {state} — RECOMMENDED ✅
   Volume: [X] | CPC: $[X] | Status: PASS

2. [City], {state}
   Volume: [X] | CPC: $[X] | Status: PASS

3. [City], {state}  (if found)
   Volume: [X] | CPC: $[X] | Status: PASS

REJECTED CITIES:
- [City]: Volume [X], CPC $[X] — REASON (volume too low / $0 CPC / CPC too high)
[list all rejected cities checked]

RECOMMENDATION: Proceed with [City], {state}
NEXT STEP: Competitor research in [City], {state}
---
""",
        expected_output=(
            "A list of 2–3 qualifying cities with volume and CPC data, "
            "all rejected cities with reasons, and a clear recommendation."
        ),
        agent=agent,
    )


def competitor_identification_task(agent, niche: str, city: str, state: str, keyword_output: str) -> Task:
    return Task(
        description=f"""
Identify the top 3 Map 3-pack competitors for '{niche}' in {city}, {state}.

Keyword list from previous phase:
{keyword_output}

Extract the 5–7 core keywords from the keyword output above.

LOCATION STRING to use in every search: "{city}, {state}, United States"

RUN THESE SEARCHES using Google Location Search tool:
For each of the 5 top core keywords, run 2 variations:
  Variation A: [keyword] {city} {state}
  Variation B: {city} {state} [keyword]

Example for concrete in Ocala FL:
  "concrete contractors Ocala FL" + "Ocala FL concrete contractors"
  "concrete company Ocala FL" + "Ocala FL concrete company"
  etc.

Run at least 10 searches total (5 keywords × 2 variations).

FOR EACH SEARCH, RECORD:
- Which businesses appear in MAPS 3-PACK
- Whether each has a website or "NO WEBSITE" (NO WEBSITE = MASSIVE GREEN FLAG ✅)
- Which businesses appear in GOOGLE ADS section (these are TOP PRIORITY PROSPECTS)
- Do NOT count: Yelp, HomeAdvisor, Angi, BBB, Home Depot, Thumbtack

TALLY: Track how many times each REAL local business appears across all searches.
Top 3 = businesses appearing most consistently (4+ times is strong signal).

Output format:
---
COMPETITOR RESEARCH — {niche.upper()} | {city.upper()}, {state.upper()}

TOP 3 COMPETITORS (Maps 3-Pack):
1. [Business Name]
   Website: [URL] or NO WEBSITE ✅ GREEN FLAG
   Appeared in: [X] of 10 searches
   Notes: [anything notable]

2. [Business Name]
   Website: [URL] or NO WEBSITE ✅ GREEN FLAG
   Appeared in: [X] of 10 searches
   Notes: [anything notable]

3. [Business Name]
   Website: [URL] or NO WEBSITE ✅ GREEN FLAG
   Appeared in: [X] of 10 searches
   Notes: [anything notable]

GOOGLE ADS ADVERTISERS FOUND (Priority Prospects for calling):
- [Business Name] | [URL]
- [Business Name] | [URL]

INITIAL SIGNALS:
[Brief 2–3 sentence summary of what you observed — strong market? weak? any obvious green flags?]

DOMAINS TO ANALYZE IN NEXT PHASE:
Competitor 1 domain: [domain.com]
Competitor 2 domain: [domain.com]
Competitor 3 domain: [domain.com or "NO WEBSITE"]
---
""",
        expected_output=(
            "Top 3 Map 3-pack competitors with websites (or no website noted), "
            "Google Ads advertisers found, and domains ready for analysis."
        ),
        agent=agent,
    )


def market_analysis_task(agent, niche: str, city: str, state: str, competitor_output: str) -> Task:
    return Task(
        description=f"""
Analyze the competitors identified for '{niche}' in {city}, {state} and deliver a GO/NO-GO verdict.

Competitor research from previous phase:
{competitor_output}

For EACH competitor with a website, run ALL FOUR of these tools:
1. Domain Age Checker — get domain age in years
2. Semrush Backlinks — get total backlinks and referring domains
3. Semrush Domain Analysis — get organic keywords and traffic
4. Website Content Analyzer — check page count and word count

For competitors with NO WEBSITE: score as MAXIMUM GREEN FLAG ✅ — skip the tools.

SCORING THRESHOLDS (apply exactly):

DOMAIN AGE:
  ✅ 0–2 years = EASY
  ⚠️  2–5 years = Moderate
  ⚠️  5–10 years = Harder
  🚫 10+ years = Red Flag

BACKLINKS:
  ✅ 0–10 = Very Weak (easy to beat)
  ⚠️  11–50 = Moderate
  ⚠️  51–97 = Heavy
  🚫 98+ = Red Flag

CONTENT DEPTH:
  ✅ No website = Massive Green
  ✅ 1–3 pages, thin content = Green
  ⚠️  4–9 pages = Moderate
  🚫 10+ service pages = Red Flag

ORGANIC PRESENCE (from Semrush Domain Analysis):
  ✅ Low/zero organic keywords = NOT ranking = Green Flag
  🚫 High organic keywords + high traffic = Ranking well = Red Flag

GO/NO-GO RULES:
  GO ✅: Overwhelming majority green — especially no websites, young domains, few backlinks
  NO-GO 🚫: Any of — all 3 on page 1, all domains 10+yr, heavy quality backlinks everywhere
  BORDERLINE ⚠️: Mixed signals — explain reasoning, lean toward NO unless very close to GO
  RULE: If it's not an overwhelming YES — it's a NO.

Output this EXACT scorecard format:
---
╔══════════════════════════════════════════════════════╗
║      DUE DILIGENCE SCORECARD                         ║
║      {niche.upper()} | {city.upper()}, {state.upper()}
╚══════════════════════════════════════════════════════╝

COMPETITOR 1: [Business Name]
Domain: [URL or NO WEBSITE]
Domain Age: [X years] — [EASY ✅ / MODERATE ⚠️ / HARDER ⚠️ / RED FLAG 🚫]
Backlinks: [X total] ([X] referring domains) — [score]
Organic Keywords: [X] — [score]
Content Depth: [X pages, ~X words] — [score]
Overall: [WEAK ✅ / MODERATE ⚠️ / STRONG 🚫]

COMPETITOR 2: [Business Name]
[same format]

COMPETITOR 3: [Business Name]
[same format]

──────────────────────────────────────────────────────
MARKET VERDICT: [GO ✅ / NO-GO 🚫 / BORDERLINE ⚠️]

REASONING: [2–3 sentences explaining the verdict based on data]

CONTENT BENCHMARK: Top competitor has ~[X] words on homepage and [X] pages.
When you build your site: aim for ~[2X] words and [X+3] pages minimum.

[If GO] NEXT STEP: Build prospect list for {city}, {state}
[If NO-GO] NEXT STEP: Try [next city from qualifying list]
──────────────────────────────────────────────────────
---
""",
        expected_output=(
            "Complete due diligence scorecard with all 3 competitors scored, "
            "GO/NO-GO verdict with reasoning, and content benchmark."
        ),
        agent=agent,
    )


def prospect_building_task(agent, niche: str, city: str, state: str, keyword_output: str) -> Task:
    return Task(
        description=f"""
Build a prospect list of 7–12 businesses already paying for advertising.
Niche: {niche} | City: {city}, {state}

Keyword list:
{keyword_output}

PRIORITY ORDER — search in this exact order:
1. Google Ads advertisers (HIGHEST — confirmed active spend right now)
2. HomeAdvisor advertisers
3. Angie's List / Angi
4. Thumbtack, Yelp

PROCESS:
Use Google Location Search tool with location: "{city}, {state}, United States"

Run searches for each core keyword + city + state:
Look at "GOOGLE ADS (Sponsored)" section in each result.
Record every advertiser domain.

For each domain found:
- Use Website Content Analyzer to vet the company (60-second check)
- SKIP if: lead gen aggregator, wrong city/state, commercial-only, wrong niche, general contractor
- ADD if: real local residential contractor, mentions {city}, performs the specific service

Also search: "homeadvisor {niche} {city} {state}" to find HomeAdvisor advertisers.

For each ADDED company:
- Record their phone number from their website
- Note owner name from About page, reviews, or Google Business Profile
- Note how you found them

VET CHECKLIST for each prospect:
✅ ADD: Local residential contractor in {niche} serving {city}
❌ SKIP: "We connect you with pros" language → lead gen, skip
❌ SKIP: Location says another state or major city not near {city}
❌ SKIP: "Commercial concrete" or "industrial" → wrong market
❌ SKIP: Does roofing + concrete + landscaping + everything → general contractor

Output format:
---
PROSPECT LIST — {niche.upper()} | {city.upper()}, {state.upper()}

#1 — [Business Name]
   Website: [URL]
   Phone: [phone number]
   Found Via: [Google Ads / HomeAdvisor / Angi / Thumbtack]
   Owner: [First Name or "Unknown"]
   Notes: [any relevant notes]

#2 — [Business Name]
[same format]

[Continue for all 7–12 prospects]

TOTAL PROSPECTS: [X]
READY TO CALL: [X] confirmed active advertisers

CALLING PRIORITY:
1. [Name] — Google Ads advertiser — [phone]
2. [Name] — Google Ads advertiser — [phone]
[etc.]
---
""",
        expected_output=(
            "A list of 7–12 qualified prospects with name, URL, phone, "
            "how found, and owner name. Sorted by calling priority."
        ),
        agent=agent,
    )


def ad_copy_task(agent, niche: str, city: str, state: str, keyword_output: str) -> Task:
    return Task(
        description=f"""
Write complete ad copy for '{niche}' in {city}, {state}.

Keyword list to draw from:
{keyword_output}

═══════════════════════════════════════
GOOGLE SMART CAMPAIGN
═══════════════════════════════════════

CHARACTER LIMITS — these are hard limits, count every character:
  Headlines: 30 characters MAX each (including spaces and punctuation)
  Descriptions: 90 characters MAX each

HEADLINE RULES: TITLE CASE — EVERY SINGLE WORD GETS CAPITALIZED
  H1: Main keyword + city (e.g. "Concrete Contractors {city}") — if over 30 chars, abbreviate city
  H2: "Get A 100% Free [Service] Quote" OR "Get A 100% Free [Service] Estimate"
  H3: Two sub-services + "And More" (e.g. "Driveways, Patios And More")

DESCRIPTION RULES: sentence case — capitalize first word ONLY
  D1: "We specialize in [sub-service], [sub-service] and more. Call today for a free [niche] quote."
  D2: "Your local affordable professional [main keyword] in the {city}, {state} area."

KEYWORD THEMES (8–10 from core list, phrases that appear as Smart Campaign dropdown options):
[List 8–10 themes directly from the keyword output above]

SETTINGS:
  Campaign type: Smart Campaign
  Goal: Calls to business
  Target: {city} + 15-mile radius
  Budget: Google recommended OR $20/day (whichever is LESS)

═══════════════════════════════════════
FACEBOOK (META) ADS
═══════════════════════════════════════

CAMPAIGN SETTINGS:
  Objective: Leads
  Buying type: Auction
  Advantage Campaign Budget: ON
  Budget: $10–$20/day

AD SET SETTINGS:
  Ad set name: top performers/winners
  Lead type: Instant Forms
  Dynamic Creative: ON
  Location: {city} + 15–20 mile radius
  Placements: Advantage+ Placements ON

PRIMARY TEXT — Write 3 variations:

Variation 1 (Pain/Price angle):
"Need [niche] but don't wanna overpay? Neither do we! Click the link for a 100% free [niche] estimate!"

Variation 2 (Personal/Local angle):
"[Sub-services] and More — [Niche] Done Right! I'm [first name], a local [niche] contractor in {city}.
I specialize in [sub-services]. No job too big or too small. Dedicated to earning your business every time."

Variation 3 (Urgency/Value angle):
"Sick of overpaying for [niche]? Get a 100% FREE estimate now and pay what's fair, not a penny more!"

HEADLINES — Write 3 variations:
1. "Get Your Free [Niche] Estimate Today!"
2. "[Niche] Done Right — Guaranteed"
3. "100% Free Estimate Now"

INSTANT FORM SETUP:
  Form type: More Volume
  Question 1: What service do you need? (Multiple choice — list the sub-services)
  Question 2: How soon do you need it? (ASAP / 24–48 hours / No rush)
  Contact fields: Full Name, Email, Phone Number (Phone REQUIRED)
  Ending: Thank you message + "We'll call you shortly. Questions? Call [tracking number]."

Output everything clearly labeled and ready to copy-paste into the ad platforms.
""",
        expected_output=(
            "Complete Google Smart Campaign ad copy (3 headlines with character counts, "
            "2 descriptions, 8–10 keyword themes, settings) and complete Facebook Ads copy "
            "(3 primary texts, 3 headlines, instant form setup). All ready to copy-paste."
        ),
        agent=agent,
    )
