# Tie-out against data.census.gov

## 1. B15003 lines: Census API pull vs data.census.gov

- 2019: 53 API rows, 53 data.census.gov rows, 50 columns each, 0 differing cells, 0 areas in one source only
- 2023: 53 API rows, 53 data.census.gov rows, 50 columns each, 0 differing cells, 0 areas in one source only
- 2025: 53 API rows, 53 data.census.gov rows, 46 columns each, 0 differing cells, 0 areas in one source only

## 2. Group counts and totals: panel.csv vs data.census.gov lines

- 2019: group counts and totals for 53 areas, 0 mismatches
- 2023: group counts and totals for 53 areas, 0 mismatches
- 2025: group counts and totals for 53 areas, 0 mismatches

## 3. Shares vs S1501 published percentages

- 2019: 265 share comparisons, 0 outside rounding (max abs diff 0.085 points)
  - share MOE, ours / S1501 direct, groups that are one line in S1501 (HS, bachelor's, graduate): median 1.03, 10th pct 0.89, 90th pct 1.15
- 2023: 265 share comparisons, 0 outside rounding (max abs diff 0.090 points)
  - share MOE, ours / S1501 direct, groups that are one line in S1501 (HS, bachelor's, graduate): median 1.02, 10th pct 0.90, 90th pct 1.18
- 2025: 265 share comparisons, 0 outside rounding (max abs diff 0.087 points)
  - share MOE, ours / S1501 direct, groups that are one line in S1501 (HS, bachelor's, graduate): median 1.03, 10th pct 0.90, 90th pct 1.15

## 4. Pay: B20004 vs data.census.gov, and national numbers

- 2015: B20004 lines 001-006 for 53 areas, 0 differing cells
- 2025: B20004 lines 001-006 for 53 areas, 0 differing cells
- R-CPI-U-RS 2015 348.300, 2025 474.994: prices up 36.4%
- National yearly change after inflation, recomputed here: median all workers 0.98%, index with own mix 0.99%, index with 2015 mix 0.48%, education mix part 0.51 points; by group: lths 1.78%, hs 0.47%, somecol 0.65%, ba 0.32%, grad -0.02%

## 5. Words on the built map page (dist/index.html)

- "Educational attainment of adults 25 and over, ${FIRST} to ${LAST}": supported (B15003 universe is the population 25 and over; map compares 2015 with 2025 (build_viz.py MAP_BASE))
- "Areas are colored only where the change passes the Census Bureau's test at 90% confidence": supported (map_template.html fillOf: hatched unless |z| > 1.645 (ACS handbook (2020) ch. 7 formula 3))
- "No standard 1-year estimates were released for 2020.": supported (user note 2021-02, https://www.census.gov/programs-surveys/acs/technical-documentation/user-notes/2021-02.html)
- "for states, and for counties and metro and micro areas with 65,000 or more people": supported (ACS 1-year publication threshold (user note 2026-06); levels mapped (DATASETS.md, Map))
- ", because they have fewer than 65,000 people.": supported (no mapped county or metro/micro shape without a 2025 value is in withheld.csv for 2025, so none was published empty)
- "table B15003 (B15002 where B15003 was published with no values)": supported (build.py fill_withheld; 851 area-years, exact match where both exist (findings_tables.md))
- "Census Bureau 2023 cartographic boundary files": supported (cb_2023_us_{state,county,cbsa}_20m, www2.census.gov/geo/tiger/GENZ2023/shp/)
- "Margins of error are at 90% confidence, approximated with the Census Bureau's formulas for derived estimates": supported (ACS handbook (2020) ch. 8 formulas 1, 6, 7)
- "the Census Bureau's test at 90% confidence": supported (ACS handbook (2020) ch. 7 formula 3)
- "In ${LAST} the survey merged its three lowest answers into one, collected less data during a federal funding lapse, and used a new population base.": supported (user notes 2026-02, 2026-04, 2026-05)
- "percentage points more than its ${LAST - 4}–${LAST - 1} trend would suggest": supported (findings_tables.md: beyond-trend group changes; numbers recomputed below)
- "Changes since ${FIRST} for this measure may include that step.": supported (states the arithmetic only, no cause)
- "Metro and micro areas are drawn with the July 2023 definitions used for ${LAST}.": supported (ACS geography boundaries by year; geo_flags.py YEAR_VINTAGE)
- "published in every year from ${FIRST} to ${LAST}, and, for metro and micro areas, only where the adult population moved less than 5% in each year its list of counties changed": supported (build_viz.py build_map: 5% rule on cbsa_changes.csv switch years after 2015)
- "Puerto Rico is shown in the inset but is not part of the national figures.": supported (ACS nation (010) excludes Puerto Rico)
- "Built by Data 4 The People": supported (house convention)
- "Median pay of workers 25 and over by education, ${FIRST} to ${LAST}": supported (B20004 universe is the population 25 and over with earnings; 2015 and 2025)
- "Pay is median earnings in the past 12 months for people 25 and over who had earnings, including part-time and part-year workers.": supported (B20004 universe: population 25 years and over with earnings (variables_B20004.json))
- "the index the Census Bureau recommends for ACS dollar figures": supported (ACS general handbook (2020) ch. 10: recommends factors based on the all-items CPI-U-RS)
- "Its ${LAST} average leaves out October ${LAST}, which was not collected during the federal funding lapse.": supported (BLS R-CPI-U-RS file note: Oct 2025 values not available due to the 2025 lapse in appropriations (data/raw/cpi/))
- "Yearly change is the compound annual growth rate: the steady yearly rate that turns the ${FIRST} value into the ${LAST} value.": supported (definition; map_template.html cagr())
- "It is an index, not a median, and the weights cover all adults, not only workers.": supported (weights are B15003 shares of the population 25 and over)
- "both can affect ${LAST} pay estimates": supported (user notes 2026-04, 2026-05; states possibility only)
- Break note numbers, recomputed here (beyond-trend change, points): less than high school -0.53, high school or more +0.53, some college or more +0.44 (the page computes them the same way at load).

**Result:** PASS on sections 1, 2, 4 and 5.
