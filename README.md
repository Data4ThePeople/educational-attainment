# Educational Attainment

This project tracks the education of adults 25 and over, from 2008 to 2025. It covers the nation, regions, divisions, states, counties, metro and micro areas, and places in the American Community Survey (ACS) 1-year estimates, which cover areas with 65,000 or more people. For years before 2025, the three lowest answers are added together to match the 2025 question.

The interactive map is `dist/index.html`, live at https://data4thepeople.github.io/educational-attainment/dist/. It covers states, counties, and metro and micro areas, with a choice of five education measures (bachelor's degree or more by default). It shows either the 2025 share or the change from 2015 to 2025, with changes colored only where they pass the Census Bureau's test at 90% confidence. Hovering over an area shows both years and the change. A Pay topic shows median earnings by education, adjusted for inflation, and the yearly change from 2015 to 2025, split into pay index growth from the change in pay within education groups and from the change in education mix. A second page, `dist/lines.html`, shows one area at a time from 2008 to 2025 and a ranked view of changes that pass the Census Bureau's test at 90% confidence.

## What's in the repo

- `DATASETS.md`: sources, years, the label-by-label variable mapping, method, and caveats.
- `FINDINGS.md`: the main changes, areas that stand out, and effects of the method and the data.
- `data/raw/`: Census API responses saved as downloaded, the data.census.gov tie-out pulls, and the OMB metro delineation files.
- `data/clean/`: the panel (`panel.csv`), area list with series breaks (`areas.csv`), change tests (`change.csv`), and check outputs.
- `scripts/`: the pipeline.
- `viz/map_template.html` and `viz/template.html`: the page templates; `scripts/build_viz.py` embeds the data.
- `data/raw/boundaries/`: Census Bureau 2023 cartographic boundary files; `scripts/build_geo.py` turns them into map shapes.

## Data sources

U.S. Census Bureau, American Community Survey 1-year estimates, tables B15003 and B15002 (educational attainment), B20004 (median earnings by educational attainment), B99151 (allocation of educational attainment) and S1501 (subject table, tie-out only), via the Census Data API and data.census.gov. Metro area county lists come from the OMB delineation files published by the Census Bureau. Prices: Bureau of Labor Statistics R-CPI-U-RS. Student debt: Federal Reserve Board, Survey of Consumer Finances 2016 and 2025, and New York Fed Consumer Credit Panel / Equifax student loan tables (static charts in `dist/charts/`). Map outlines come from the Census Bureau's 2023 cartographic boundary files (1:20,000,000).

## Rebuild

```
python scripts/fetch.py        # needs CENSUS_API_KEY via ~/.claude/d4tp-process/d4tp_env.py
python scripts/build.py
python scripts/geo_flags.py
python scripts/findings.py
python scripts/build_geo.py
python scripts/build_viz.py
python scripts/pay_findings.py
python scripts/post_charts.py  # post charts and the 1680x1080 hero
python scripts/tooltip_screenshot.py   # needs Google Chrome
python scripts/map_screenshot.py       # map for the email; needs Google Chrome
python scripts/fetch_scf.py    # Survey of Consumer Finances files (not committed)
python scripts/scf_debt.py
python scripts/debt_charts.py
python scripts/credit_debt.py
python scripts/tieout.py       # checks against data.census.gov
```

Python 3.9 with pandas, numpy, requests, xlrd, openpyxl, pyshp and shapely.

## Method notes

- Shares, not counts, are the main measure, because the 2025 population controls changed.
- Lines are mapped by label, not line number, because the 2025 table layout changed.
- Margins of error use the formulas in the Census Bureau's *Understanding and Using American Community Survey Data* (2020), chapters 7 and 8.
- There is no standard 2020 1-year release, so 2020 is a gap.
- The 2025 question change also moved part of the "less than high school" and "some college" shares. The pages note the 2024 to 2025 step for the measures that include those groups. See `DATASETS.md`.
- Pay is in 2025 dollars using the R-CPI-U-RS, which the Census Bureau recommends for ACS dollar figures. Yearly change is the compound annual growth rate. The held-mix measure is an index (a weighted average of group medians), not a median.
- Where B15003 was published with no values, the same five groups come from B15002.
