# Pre-loaded keyword lists for known niches.
# Phase 1 uses these instead of making Ahrefs API calls.
# Volumes are national figures — stable enough to cache.
# CPC is NOT cached. It is always looked up fresh per city in Phase 2 via Ahrefs City Keyword Check.

KEYWORD_CACHE: dict[str, str] = {

    "concrete": """---
NICHE: CONCRETE

CORE KEYWORDS (5–7):
1. concrete contractor  | Volume: 33,100/mo
2. stamped concrete     | Volume: 49,500/mo
3. concrete staining    | Volume: 40,500/mo
4. concrete company     | Volume: 12,100/mo
5. concrete resurfacing | Volume: 14,800/mo
6. polished concrete    | Volume: 14,800/mo
7. concrete driveway    | Volume: 12,100/mo

RAW LIST (all researched):
concrete contractor     | Volume: 33,100
concrete specialist     | Volume:    510
concrete company        | Volume: 12,100
stamped concrete        | Volume: 49,500
concrete staining       | Volume: 40,500
concrete driveway       | Volume: 12,100
concrete patio          | Volume: 12,100
polished concrete       | Volume: 14,800
concrete polishing      | Volume: 14,800
concrete resurfacing    | Volume: 14,800
concrete repair         | Volume:  9,900
decorative concrete     | Volume:  5,400
concrete coating        | Volume:  4,400
concrete service        | Volume:  2,400
concrete walkway        | Volume:  1,600
flatwork concrete       | Volume:  1,300
concrete installation   | Volume:  1,300
concrete installers     | Volume:  1,300
concrete by the yard    | Volume:    880

PRIMARY KEYWORD (strongest for city checks): concrete contractor
---""",


    "tree service": """---
NICHE: TREE SERVICE

CORE KEYWORDS (5–7):
1. tree service          | Volume: 60,500/mo
2. stump grinding        | Volume: 49,500/mo
3. tree removal          | Volume: 40,500/mo
4. tree trimming         | Volume: 40,500/mo
5. stump removal         | Volume: 18,100/mo
6. tree cutting service  | Volume: 14,800/mo
7. tree cutting          | Volume: 12,100/mo

RAW LIST (all researched):
tree service               | Volume: 60,500
stump grinding             | Volume: 49,500
tree removal               | Volume: 40,500
tree trimming              | Volume: 40,500
stump removal              | Volume: 18,100
tree cutting service       | Volume: 14,800
tree cutting               | Volume: 12,100
tree pruning               | Volume:  8,100
shrub trimming             | Volume:  1,300
shrub removal              | Volume:  1,000
tree service company       | Volume:  1,000
tree planting services     | Volume:    880
local tree service companies | Volume:  260

PRIMARY KEYWORD (strongest for city checks): tree service
---""",


    "fencing": """---
NICHE: FENCING

CORE KEYWORDS (5–7):
1. fence company near me      | Volume: 165,000/mo
2. fencing                    | Volume:  90,500/mo
3. privacy fence              | Volume:  74,000/mo
4. fence contractors          | Volume:  40,500/mo
5. fence installation near me | Volume:  33,100/mo
6. fence installation         | Volume:  27,100/mo
7. fence installers           | Volume:  27,100/mo

RAW LIST (all researched):
fence company near me      | Volume: 165,000
fencing                    | Volume:  90,500
chain link fence           | Volume:  90,500  [product/supply — secondary]
privacy fence              | Volume:  74,000
fence panels               | Volume:  60,500  [DIY supply — skip]
vinyl fence                | Volume:  49,500  [product/supply — secondary]
fence contractors          | Volume:  40,500
invisible fence for dogs   | Volume:  33,100  [brand product — skip]
fence installation near me | Volume:  33,100
dog fence                  | Volume:  33,100  [DIY — skip]
fence installation         | Volume:  27,100
fence installers           | Volume:  27,100
pool fence                 | Volume:  22,200
electric fence             | Volume:  22,200  [agricultural/DIY — skip]
fencing near me            | Volume:  18,100
electric dog fence         | Volume:   9,900  [DIY — skip]
deer fence                 | Volume:   9,900  [DIY — skip]
composite fencing          | Volume:   8,100
temporary fencing          | Volume:   8,100  [rental/events — skip]
underground dog fence      | Volume:   8,100  [DIY — skip]
fencing contractors        | Volume:   6,600
fence builders             | Volume:   6,600
composite fence panels     | Volume:   4,400  [supply — skip]
best fence company near me | Volume:   3,600
local fence companies      | Volume:   1,900

PRIMARY KEYWORD (strongest for city checks): fence contractors
---""",

}
