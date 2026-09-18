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
        "FL": "Ocala, Lakeland, Cape Coral, Gainesville, Pensacola, Port St. Lucie, Palm Bay, Kissimmee, Leesburg, Sarasota, Melbourne, Daytona Beach",
        "TX": "Lubbock, Amarillo, Waco, Midland, Killeen, Beaumont, McKinney, Pearland, Abilene, Tyler, Longview, Lewisville",
        "GA": "Marietta, Augusta, Columbus, Savannah, Macon, Warner Robins, Athens, Kennesaw, Smyrna, Valdosta, Woodstock, Newnan",
        "NC": "Fayetteville, Concord, Gastonia, High Point, Wilmington, Burlington, Greenville, Huntersville, Jacksonville, Kannapolis, Hickory, Wilson",
        "AZ": "Gilbert, Surprise, Avondale, Peoria, Goodyear, Yuma, Prescott, Casa Grande, Maricopa, Queen Creek, Kingman, Lake Havasu City",
        "TN": "Murfreesboro, Knoxville, Chattanooga, Clarksville, Jackson, Smyrna, Hendersonville, Johnson City, Cookeville, Spring Hill, Columbia, Maryville",
        "SC": "Columbia, Greenville, Spartanburg, Rock Hill, Summerville, Myrtle Beach, Florence, Aiken, Conway, Greer, Lexington, Anderson",
        "AL": "Huntsville, Mobile, Tuscaloosa, Dothan, Auburn, Decatur, Madison, Florence, Phenix City, Prattville, Alabaster, Athens",
        "LA": "Shreveport, Lafayette, Lake Charles, Bossier City, Monroe, Alexandria, Slidell, New Iberia, Houma, Hammond, Zachary, Ruston",
        "NV": "Henderson, Reno, Sparks, North Las Vegas, Carson City, Pahrump, Fernley, Elko, Mesquite, Boulder City, Fallon, Laughlin",
        "VA": "Chesapeake, Newport News, Hampton, Roanoke, Lynchburg, Fredericksburg, Charlottesville, Suffolk, Harrisonburg, Danville, Manassas, Blacksburg",
        "OK": "Norman, Broken Arrow, Edmond, Lawton, Moore, Stillwater, Enid, Muskogee, Owasso, Bixby, Bartlesville, Shawnee",
        "UT": "Provo, Ogden, St. George, Orem, West Jordan, Sandy, South Jordan, Lehi, Draper, Clearfield, Layton, Riverton",
        "AR": "Fort Smith, Fayetteville, Springdale, Jonesboro, Conway, Rogers, Bentonville, Hot Springs, Benton, Bryant, Russellville, Searcy",
        "MS": "Gulfport, Biloxi, Hattiesburg, Southaven, Tupelo, Meridian, Olive Branch, Clinton, Pearl, Madison, Brandon, Starkville",
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

CITIES TO CHECK in {state} (check in this order):
{suggestions}

AVOID: Major metros (Orlando, Tampa, Miami, Dallas, Phoenix, Las Vegas, Nashville, Houston)
PREFER: Cities 50,000–250,000 population

PROCESS — follow this EXACTLY:
1. Take the PRIMARY KEYWORD from the keyword output above
2. Check cities ONE AT A TIME in the order listed above using Semrush City Keyword Check:
   - keyword = the PRIMARY KEYWORD
   - city = the city name
   - state = {state} (2-letter abbreviation)
3. Record Volume and CPC for each city checked
4. The tool will return a PASS or FAIL — trust the tool's verdict exactly
5. *** STOP IMMEDIATELY once you have found 3 cities that PASS *** — do NOT check more cities
6. If you reach the end of the list with fewer than 3 passes, report what you found
7. Recommend the strongest qualifying city (highest volume within the CPC range)

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

IF NO CITIES PASS BOTH CRITERIA — output this exact block instead of the above:
---
CITY RESEARCH — {state.upper()}
NO QUALIFYING CITIES FOUND

All cities checked failed on CPC ($0 or $5+) or volume (<30).

REJECTED CITIES:
[list every city checked with: Volume, CPC, reason for rejection]

RECOMMENDATION: No qualifying cities in {state}. Try a different state.
---
""",
        expected_output=(
            "A list of 2–3 qualifying cities with volume and CPC data, "
            "all rejected cities with reasons, and a clear recommendation. "
            "If no cities qualify, output 'NO QUALIFYING CITIES FOUND' with all rejected cities listed."
        ),
        agent=agent,
    )


def competitor_identification_task(agent, niche: str, city: str, state: str, keyword_output: str) -> Task:
    return Task(
        description=f"""
Identify the top 3 Map 3-pack competitors for '{niche}' in {city}, {state}.
Follow the Flat Fee Mastery market research process exactly.

Keyword list from previous phase:
{keyword_output}

Extract the 5–6 core keywords from the keyword output above.

LOCATION STRING to use in every search: "{city}, {state}, United States"

═══════════════════════════════════════════════════
STEP 1 — RUN 10+ SEARCHES (5 keywords × 2 variations each)
═══════════════════════════════════════════════════
For each of the 5–6 core keywords, run BOTH variations:
  Variation A: [keyword] {city} {state}         ← e.g. "concrete contractors {city} {state}"
  Variation B: {city} {state} [keyword]         ← e.g. "{city} {state} concrete contractors"

Run ALL 10+ searches. Do not skip any.

FOR EACH SEARCH, RECORD:
- Which businesses appear in the MAPS 3-PACK (ignore Yelp, HomeAdvisor, Angi, BBB, Thumbtack)
- Whether each business has a website or "NO WEBSITE" (NO WEBSITE = MASSIVE GREEN FLAG ✅)
- Which businesses appear in the GOOGLE ADS / SPONSORED section (priority prospects)

═══════════════════════════════════════════════════
STEP 2 — TALLY & IDENTIFY TOP 3
═══════════════════════════════════════════════════
Count how many times each REAL local business appeared across all searches.
PRIMARY THRESHOLD: A business appearing 4+ times = top competitor.
FALLBACK: If no business hits 4+, use 3+ as the threshold.
POSITIVE SIGNAL: If results are totally inconsistent (different companies every search with
  no overlap) — that is a GREEN FLAG. It means Google has no reliable go-to in this market.
  There is a vacancy. Note this explicitly.

If you cannot find 3 map competitors, supplement with ORGANIC results (the regular blue links
below the map). Pick the first REAL company website — not an aggregator.

═══════════════════════════════════════════════════
STEP 3 — CHECK ORGANIC PAGE 1 PRESENCE
═══════════════════════════════════════════════════
For each of your top 3 competitors that HAS a website, run one more search:
  Search: [their domain] + [primary keyword] + {city}
  OR search the primary keyword and check if their domain appears in the blue organic links.

Note for each competitor: DO THEY APPEAR on page 1 organically? YES or NO.
If NONE of the top 3 rank organically on page 1 → STRONG GO SIGNAL ✅
If ALL 3 rank organically on page 1 → RED FLAG 🚫 (real entrenched competition)

Output format:
---
COMPETITOR RESEARCH — {niche.upper()} | {city.upper()}, {state.upper()}

SEARCHES RUN: [list all 10+ search queries]

TOP 3 COMPETITORS (Maps 3-Pack):
1. [Business Name]
   Website: [URL] or NO WEBSITE ✅ GREEN FLAG
   Appeared in: [X] of [total] searches
   Ranks organically page 1: YES / NO
   Notes: [anything notable — old phone number, out-of-area, thin site, etc.]

2. [Business Name]
   Website: [URL] or NO WEBSITE ✅ GREEN FLAG
   Appeared in: [X] of [total] searches
   Ranks organically page 1: YES / NO
   Notes: [anything notable]

3. [Business Name]
   Website: [URL] or NO WEBSITE ✅ GREEN FLAG
   Appeared in: [X] of [total] searches
   Ranks organically page 1: YES / NO
   Notes: [anything notable]

GOOGLE ADS ADVERTISERS FOUND (Priority Prospects for Phase 5):
- [Business Name] | [URL]
- [Business Name] | [URL]

ORGANIC RANKING SUMMARY:
[X] of 3 competitors rank on page 1 organically.
[STRONG GO SIGNAL ✅ / CAUTION ⚠️ / RED FLAG 🚫] — [one sentence explanation]

INITIAL MARKET SIGNALS:
[2–3 sentence summary — strong market? weak? any obvious green flags like no websites?]

DOMAINS TO ANALYZE IN NEXT PHASE:
Competitor 1 domain: [domain.com]
Competitor 2 domain: [domain.com]
Competitor 3 domain: [domain.com or "NO WEBSITE"]
---
""",
        expected_output=(
            "Top 3 Map 3-pack competitors with websites (or no website noted), "
            "appearance tally across all searches, organic page 1 check for each, "
            "Google Ads advertisers found, and domains ready for analysis."
        ),
        agent=agent,
    )


def market_analysis_task(agent, niche: str, city: str, state: str, competitor_output: str) -> Task:
    return Task(
        description=f"""
Analyze the competitors identified for '{niche}' in {city}, {state} and deliver a GO/NO-GO verdict.
Follow the Flat Fee Mastery due diligence process — 4 metrics per competitor.

Competitor research from previous phase:
{competitor_output}

═══════════════════════════════════════════════════
FOR EACH COMPETITOR WITH A WEBSITE — run all 4 checks:
═══════════════════════════════════════════════════

METRIC 1 — DOMAIN AGE:
  Use Domain Age Checker tool. Record year created and age in years.
  ✅ 0–2 years = EASY | ⚠️ 2–5 years = Moderate | ⚠️ 5–10 years = Harder | 🚫 10+ years = Red Flag

METRIC 2 — BACKLINKS:
  Use Semrush Backlinks tool. Record total backlinks and referring domains.
  ✅ 0–10 = Very Weak (easy to beat) | ⚠️ 11–50 = Moderate | ⚠️ 51–97 = Heavy | 🚫 98+ = Red Flag
  Note: foreign/spammy links are worthless — quality matters more than count.

METRIC 3 — CONTENT DEPTH:
  Use Website Content Analyzer. Count pages and check word count.
  ✅ 1–3 pages, thin content = Green | ⚠️ 4–9 pages = Moderate | 🚫 10+ service pages = Red Flag

METRIC 4 — ORGANIC PAGE 1 PRESENCE:
  Use Google Location Search to verify whether this competitor's domain appears
  in the organic blue-link results (below the map) for your primary keyword in {city}.
  Search: "[primary niche keyword] {city} {state}" and look for their domain.
  ✅ NOT on page 1 organically = Green Flag | 🚫 Appearing on page 1 = Red Flag

FOR COMPETITORS WITH NO WEBSITE:
  Skip all 4 tools. Score as MAXIMUM GREEN FLAG ✅ across all metrics.
  No website = they are ranking purely by default. You will leapfrog them immediately.

═══════════════════════════════════════════════════
GO / NO-GO DECISION RULES (apply exactly):
═══════════════════════════════════════════════════
GO ✅:   Overwhelming majority green — especially: no websites, young domains (0–2yr),
         very few backlinks (0–10), thin/no content, NOT ranking organically.
NO-GO 🚫: ANY of these is disqualifying:
         - ALL 3 competitors rank on page 1 organically for majority of keywords
         - ALL domains are 10+ years old
         - Heavy quality backlink profiles across all 3 competitors (50+ each)
BORDERLINE ⚠️: Mixed signals — explain clearly, lean NO unless it is very close to GO.
RULE: If it's not an overwhelming YES — it's a NO. Find another city.

Output this EXACT scorecard format:
---
╔══════════════════════════════════════════════════════╗
║      DUE DILIGENCE SCORECARD                         ║
║      {niche.upper()} | {city.upper()}, {state.upper()}
╚══════════════════════════════════════════════════════╝

COMPETITOR 1: [Business Name]
Domain: [URL or NO WEBSITE ✅]
Domain Age: [X years, created YYYY] — [EASY ✅ / MODERATE ⚠️ / HARDER ⚠️ / RED FLAG 🚫]
Backlinks: [X total] ([X] referring domains) — [VERY WEAK ✅ / MODERATE ⚠️ / HEAVY ⚠️ / RED FLAG 🚫]
Content Depth: [X pages, ~X words] — [GREEN ✅ / MODERATE ⚠️ / RED FLAG 🚫]
Ranks on Page 1 Organically: [YES 🚫 / NO ✅]
Overall Threat Level: [WEAK ✅ / MODERATE ⚠️ / STRONG 🚫]

COMPETITOR 2: [Business Name]
[same format]

COMPETITOR 3: [Business Name]
[same format]

──────────────────────────────────────────────────────
ORGANIC RANKING SUMMARY:
[X] of 3 competitors found on page 1 organically.
[STRONG GO SIGNAL ✅ / CAUTION ⚠️ / DISQUALIFYING RED FLAG 🚫]

MARKET VERDICT: [GO ✅ / NO-GO 🚫 / BORDERLINE ⚠️]

REASONING: [2–3 sentences citing specific data — which green flags tipped the scale]

CONTENT BENCHMARK: Top competitor has ~[X] words on their homepage and [X] total pages indexed.
To beat them: aim for ~[2X] words and at least [X+3] pages on your site.

[If GO] NEXT STEP: Build prospect list for {city}, {state}
[If NO-GO] NEXT STEP: Try the next qualifying city from the city research phase.
──────────────────────────────────────────────────────
---
""",
        expected_output=(
            "Complete 4-metric due diligence scorecard for all 3 competitors "
            "(domain age, backlinks, content depth, organic page 1 ranking), "
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

⚠️ NEVER CLICK ON GOOGLE ADS — type the advertiser's URL directly into the browser bar.
Clicking an ad costs them money and will poison the relationship before you even call.
The tool returns URLs from the API so you can type them directly — always do this.

For each domain found:
- Use Website Content Analyzer to vet the company (60-second check)
- SKIP if: lead gen aggregator, wrong city/state, commercial-only, wrong niche, general contractor
- ADD if: real local residential contractor, mentions {city}, performs the specific service

Also search these to find more advertisers (in priority order):
- "homeadvisor {niche} {city} {state}"
- "angi {niche} {city} {state}"
- "thumbtack {niche} {city} {state}"
- "yelp {niche} {city} {state}"

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
  Dynamic Creative: ON  ← turn ON at the AD SET level only
  Location: {city} + 15–20 mile radius
  Placements: Advantage+ Placements ON

AD SETTINGS (inside the ad set):
  Dynamic Creative: OFF  ← must be OFF at the individual ad level
  CTA button: Get Quote  ← use exactly this CTA on every ad

CREATIVE ASSETS (user must prepare before launching):
  Images: 3 square images at 600×600px — use real job photos, before/after shots, or team photos
  Do NOT use stock photos — authentic local images perform best

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
