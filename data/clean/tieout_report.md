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

## 4. Words on the built page (dist/index.html)

- "Educational attainment of adults 25 and over, 2008 to 2025": supported (B15003 universe is the population 25 and over; series runs 2008-2025 (DATASETS.md))
- "for the nation, states, counties, metro areas and places with 65,000 or more people": supported (ACS 1-year publication threshold; levels pulled (DATASETS.md, Geography))
- "the three lowest answers are added together to match the 2025 question": supported (user note 2026-02; mapping in DATASETS.md)
- "No standard 1-year estimates were released for 2020": supported (Census Bureau released only experimental 2020 1-year estimates)
- "B15002 fills years where B15003 was withheld": supported (build.py fill_withheld; 851 area-years, exact match where both exist (findings_tables.md))
- "Bands show the 90% margin of error, from the Census Bureau's formulas for derived estimates": supported (ACS handbook (2020) ch. 8 formulas 1, 6, 7)
- "pass the Census Bureau's test at 90% confidence": supported (ACS handbook (2020) ch. 7 formula 3)
- "In ${LAST} the survey merged its three lowest answers into one": supported (user note 2026-02)
- "percentage points more than its recent trend, and the change shows up mostly in "some college."": supported (findings_tables.md: beyond-trend group changes; number recomputed below)
- "Built by Data 4 The People": supported (house convention)
- Break note number, recomputed here: 0.5 points (the page computes it the same way at load).
- Level names: "Places (cities, towns and CDPs)" covers census-designated places, which are not cities; supported.

**Result:** PASS on sections 1, 2 and 4.
