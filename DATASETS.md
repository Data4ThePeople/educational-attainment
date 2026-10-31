# Datasets

One section per dataset, written before the analysis and updated as it turned
things up. Numbers quoted here come from `data/clean/findings_tables.md`, which
`scripts/findings.py` writes.

## B15003: Educational Attainment for the Population 25 Years and Over (Census Bureau, ACS 1-year)

**What it is.** The number of people 25 and over in an area, by the highest
level of school they completed or the highest degree they received. One row per
area per year. The lines don't overlap and add up to the table total (checked
for every row by `scripts/build.py`).

**Where it comes from.** Census Data API,
`https://api.census.gov/data/<year>/acs/acs1?get=NAME,group(B15003)&for=<level>`.
JSON, free, key loaded from the central `.env` with `d4tp_env.py`. Each
response is saved unchanged in `data/raw/<year>/`, with that year's variable
labels in `variables_B15003.json`.

**Version and vintage.** One release per year, each September, for the prior
calendar year. Pulled October 29, 2026. Years used: 2008–2019 and 2021–2025.

- B15003 does not exist in the 1-year files before 2008 (the API returns 404
  for 2005, 2006 and 2007).
- There is no standard 2020 1-year release. The Census Bureau released only
  experimental estimates for 2020, because the pandemic cut response. We leave
  2020 as a gap. We do not interpolate it or use the experimental estimates.
  (User note 2021-02,
  https://www.census.gov/programs-surveys/acs/technical-documentation/user-notes/2021-02.html)

**Could B15002 give a longer series?** B15002 (by sex) exists from 2005, and
summing the two sexes gives the same five groups. We do not use it to extend
the series back:

- The attainment question was revised in 2008. It added separate Nursery and
  Kindergarten boxes and a write-in for grades 1 to 11, and it split "High
  school graduate (including GED)" into "Regular high school diploma" and "GED
  or alternative credential." The Census Bureau tested this in the 2006 ACS
  Content Test and warned that it may introduce an inconsistency between 2007
  and 2008 (Crissey, *Evaluation Report Covering Educational Attainment*, 2007,
  https://www.census.gov/library/working-papers/2007/acs/2007_Crissey_02.html).
- The 2005 ACS left out people living in group quarters (dorms, prisons,
  nursing homes). They were added in 2006.

So a B15002 series would cross a question change in 2008, and in 2005 it would
also cover a different population. We use B15002 from 2008 on as a cross-check
and to fill withheld years (see its section).

**Coverage.** Areas with 65,000 or more people in the year, at the levels we
pull: nation, region, division, state (plus DC), Puerto Rico (kept apart and
not in the national total), county, metro and micro area, and place. Puerto
Rico's municipios, metro areas and places are in the county, metro and place
lists. Areas published per year (from `findings_tables.md`):

| Level | 2008 | 2019 | 2025 | Ever published | In every year |
|---|---|---|---|---|---|
| County | 802 | 840 | 863 | 880 | 782 |
| Metro and micro area | 512 | 518 | 536 | 596 | 457 (346 in the ranked view) |
| Place | 532 | 634 | 672 | 691 | 498 |

**Changes over time.**

- *2008:* question revised (see above). B15003 starts here.
- *2019:* labels gain a trailing colon on totals ("Total:"). The mapping strips it.
- *2025:* the three lowest answers, "No schooling completed," "Nursery or
  preschool" and "Kindergarten," were replaced by one answer, "Less than grade
  1." The 2025 table has 23 lines, not 25, and every line from "1st grade" down
  sits two numbers lower (for example, "Bachelor's degree" is B15003_022
  through 2024 and B15003_020 in 2025). User note 2026-02 says B15002 and
  B15003 can be compared with earlier years by adding up the three old lines,
  and that C15003 should not be compared. It gives the reason for the change:
  in testing, the old answer list pushed too many people into "No schooling
  completed" and raised the share below first grade.
  (https://www.census.gov/programs-surveys/acs/technical-documentation/user-notes/2026-02.html)

We map every line by its label, read from that year's `variables.json`, never
by line number. The build stops on any label it does not recognize. The full
mapping is in "Variable mapping" below and in `data/clean/mapping_B15003.csv`.

**What the 2025 change does to the five groups (checked with the data).** We
expected the change to stay inside "less than high school," since all three old
answers and the new one sit in that group. The data does not fully support
that:

- Nationally, the less-than-grade-1 share fell from 2.13% in 2024 to 0.77% in
  2025, 1.40 points more than its 2021–2024 trend. It fell in all 50 states and
  DC (significant in 49).
- Only about 0.9 points of that shows up elsewhere inside less than high school
  (mostly grades 10, 11 and 12 with no diploma). The rest shows up outside it:
  beyond-trend changes were +0.33 points in "some college, less than 1 year,"
  +0.19 in "some college, 1 or more years," and +0.14 in GED.
- By group, the 2024–2025 change beyond trend was −0.53 points for less than
  high school and +0.55 for some college or associate's, against +0.09 for high
  school, −0.11 for bachelor's and 0.00 for graduate.
- Across areas, places with a bigger drop in less than grade 1 had a bigger
  unusual drop in less than high school (slope +0.5 to +0.8, correlation about
  +0.3 for states, counties and metro areas), and a bigger unusual rise in some
  college.

So less than high school and some college carry part of the question change in
2025, roughly half a point nationally. High school, bachelor's and graduate do
not show it. The 2025 MOE widening, the new population controls and the
collection lapse could also move 2025 values, and this check cannot fully
separate them from the question change. The cross-area pattern links the shift
to the less-than-grade-1 drop, but that is a pattern, not proof of cause. The
result does not depend on the trend base: with any base year from 2008 to 2022,
less than high school falls 0.41 to 0.57 points beyond trend and some college
rises 0.40 to 0.59. In the viz, the 2024 to 2025 step
for those two groups is dashed and carries a note. The less-than-grade-1 line
itself is not charted across 2025.

**Withheld tables.** The Census Bureau publishes B15003 with no values for some
areas over 65,000 in some years. Its data-suppression page does not give the
rule; we have not confirmed the reason. This happened in 1,049 area-years, mostly places, and became
more common over time (25 area-years in 2008, 113 in 2024, 97 in 2025). B15002 is
published for 851 of those. Where both tables exist, their five-group counts
and totals match exactly in all 33,346 area-years. So we fill the 851 from
B15002 and mark them (`source` column in `panel.csv`). The other 198 are
dropped and listed in `data/clean/withheld.csv`. The fill keeps 98 areas in
the every-year panel (10 metro areas, 17 counties, 71 places). Set
`FILL_FROM_B15002 = False` in `scripts/build.py` to turn it off.

**Annotation codes.** The API can return codes in place of a value:
`-555555555` in an MOE means the estimate is controlled and has no sampling
error (we use 0); `-222222222`, `-333333333`, `-666666666`, `-888888888` and
`-999999999` mean the value could not be computed or is not available. Rows
with these are flagged (`bad_values` in `areas.csv`).

**User note 2026-06.** From 2025, household record swapping is no longer
applied to 1-year tables, and three release rules were dropped (the 500,000
population floor for sub-population profiles and subject tables, the "rule of
3" for aggregates, and the "rule of 50" for some sub-population tables). The
65,000 threshold is unchanged, and the note says the older data-quality rules
stay. The number of areas published rose by a similar amount in 2025 as in
earlier years (places 657 to 672, counties 861 to 863), and B15003 was still
withheld for 97 area-years. We see no sign that the change added areas to this
table.
(https://www.census.gov/programs-surveys/acs/technical-documentation/user-notes/2026-06.html)

**Missing data.** Missing answers are filled in by the Census Bureau before
tabulation. See B99151.

**Revisions.** The Census Bureau does not revise published 1-year estimates.

**Units and rounding.** Counts of people, whole numbers. MOEs at 90%
confidence. Shares are ours (count divided by the table total).

**Population controls.** The ACS weights each year's sample so totals by age,
sex, race and Hispanic origin match the Census Bureau's population estimates
for that year. User note 2026-05: the 2025 controls (Vintage 2025) start from
the 2020 Census through the Modified Age and Race Census file, not the "blended
base" used since 2021. Counts can shift in 2025 for that reason alone. Shares
are less exposed, but not immune: the controls set the age and race mix, and
attainment differs by age and race. This is why the main measure is shares.
Nationally the population 25 and over grew 1.05% from 2024 to 2025, within the
range of earlier years (0.66% to 1.78%).
(https://www.census.gov/programs-surveys/acs/technical-documentation/user-notes/2026-05.html)

**Known quirks.**

- *Metro area codes carry the delineation vintage.* The Census `GEO_ID` for a
  metro area includes a vintage component (`310M100US…` through
  `310M700US…`), so the same metro gets a new `GEO_ID` with each OMB update.
  We track metro areas by the 5-digit CBSA code (`310XX00US<code>`) and keep
  the raw `GEO_ID` in `panel.csv`.
- *Metro delineations used by each ACS year* (ACS "Geography Boundaries by
  Year" pages; bulletin numbers from the Census Bureau's OMB bulletin list):
  2009 November 2008 (09-01); 2010–2012 December 2009 (10-02); 2013–2015
  February 2013 (13-01); 2016–2017 July 2015 (15-01); 2018 August 2017 (17-01);
  2019 September 2018 (18-04); 2021–2022 March 2020 (20-01); 2023–2025 July
  2023 (23-01). The Census Bureau does not state which one 2008 used; we assume
  November 2007.
- *County changes that matter at this threshold.* Connecticut replaced its
  eight counties with nine planning regions in the 2022 ACS (old codes end in
  2021, new ones start in 2022). Bedford city, Virginia, became part of Bedford
  County in 2013 (the county is larger from 2014). Other county changes in
  2008–2025 were in Alaska and South Dakota, in areas well under 65,000.
- *Places* use boundaries as of January 1 of the data year, so annexations
  change them every year. We do not track annexations. In 2014 the boundary
  update was suspended and 2013 boundaries were used.

**Uncertainty.** Every estimate has a published MOE at 90% confidence.

User note 2026-04: a lapse in federal funding stopped ACS data collection for
about six weeks in 2025. It affected the August through November monthly
samples: mailings were canceled or delayed, and in-person follow-up was
canceled for the August and September samples. The note says the smaller final
sample noticeably lowered response rates and widened the MOEs for all 2025
estimates. It does not describe any change to the weighting.
(https://www.census.gov/programs-surveys/acs/technical-documentation/user-notes/2026-04.html)

Measured here: the median MOE of the bachelor's share rose 7% to 11% from 2024
to 2025 at each level (states 0.42 to 0.46 points, places 2.76 to 3.06). For
less than high school the rise was 2% to 7%. Tests against 2025 are a little
less likely to pass than they would be with a normal sample.

**License and attribution.** Public domain (U.S. government work). Credit:
"U.S. Census Bureau, American Community Survey 1-year estimates, tables B15003
and B15002."

## B15002: Sex by Educational Attainment for the Population 25 Years and Over (Census Bureau, ACS 1-year)

**What it is.** The same attainment answers, split by sex, with grades grouped
more coarsely. Used here as a cross-check of B15003 and to fill area-years
where B15003 is withheld.

**Where it comes from.** Same API, `group(B15002)`. Saved in `data/raw/`.

**Changes over time.** Exists from 2005. In 2025 its two lowest lines changed:

| Years | Line 003 / 020 | Line 004 / 021 |
|---|---|---|
| 2005–2024 | No schooling completed | Nursery to 4th grade |
| 2025 | Less than grade 1 | 1st to 4th grade |

Nursery and Kindergarten were never published as their own lines in B15002;
they sat inside "Nursery to 4th grade." So the fix in user note 2026-02 (add up
the three old answers) cannot be done with B15002 alone. B15002 lines up across
2025 only at "less than 5th grade" (lines 003 + 004 for each sex). That share
fell from 2.59% in 2024 to 1.24% in 2025 nationally, close to the drop in
B15003's less-than-grade-1 share.

The high school line was labeled "High school graduate, GED, or alternative"
in some years and "High school graduate (includes equivalency)" in others. Both
map to the same group.

**Check against B15003.** In all 33,346 area-years where both tables have
values, the five-group shares and the totals match exactly.

**Uncertainty.** Summing the two sexes adds MOEs with the root-sum-of-squares
formula, so B15002 MOEs differ a little from B15003's for the same group.

**License and attribution.** Public domain. U.S. Census Bureau, ACS 1-year,
table B15002.

## B99151: Allocation of Educational Attainment for the Population 25 Years and Over (Census Bureau, ACS 1-year)

**What it is.** How many people 25 and over had their attainment answer filled
in by the Census Bureau (allocated) rather than reported. Labeled "Imputed" /
"Not imputed" in 2008 and "Allocated" / "Not allocated" later.

**How the filling works.** When a person's answer is missing or doesn't fit
with their other answers, the Census Bureau takes the answer of a similar
person nearby who did answer ("hot-deck" allocation), matched on traits such
as age and sex. Allocated answers are counted in B15003 like any other.

**Source coverage check.** Share of attainment answers that were filled in
(from `findings_tables.md`):

| | 2008 | 2012 | 2013 | 2019 | 2021 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Nation | 4.6% | 5.1% | 7.1% | 7.9% | 9.8% | 9.6% | 10.2% |
| Median county | 3.9% | 4.2% | 6.2% | 6.5% | 8.7% | 8.5% | 9.0% |
| Highest place | 25.0% | 17.4% | 20.9% | 41.0% | 37.1% | 25.7% | 23.8% |

The filled-in share roughly doubled over the period, with steps up in 2013 and
2021, and 2025 is the highest year nationally. By 2025, about one adult in ten
nationally has an attainment answer the Census Bureau filled in. In a few
places in some years it is a quarter or more. The ACS doesn't publish
measured and filled values separately for B15003, so the viz cannot show them
apart. The post should say this.

## S1501: Educational Attainment, subject table (Census Bureau, ACS 1-year)

**What it is.** The Census Bureau's own percentages for the population 25 and
over, with MOEs computed directly from the survey (replicate weights), not from
the approximation formulas.

**Use here.** Tie-out only, for 2019, 2023 and 2025, nation and states, pulled
from data.census.gov. Our shares match its percentages within rounding in all
795 comparisons. For groups that are one line in S1501 (high school, bachelor's,
graduate), our approximated share MOEs are a median of 1.02 to 1.03 times its
direct MOEs (10th to 90th percentile, 0.89 to 1.18).

## B20004: Median Earnings in the Past 12 Months by Sex by Educational Attainment for the Population 25 Years and Over (Census Bureau, ACS 1-year)

**What it is.** Median earnings for people 25 and over with earnings, in the
survey year's dollars, overall and for the same five education groups as
B15003 (lines 001 to 006; the sex lines are not used). Covers part-time and
part-year workers.

**Pulled.** 2015 to 2025 (no 2020), for the nation, states, counties and
metro and micro areas, by `scripts/fetch.py`, into
`data/raw/<year>/B20004_<level>.json`. The map uses 2015 and 2025. No value
in those years is null or an annotation code. Labels are checked by line in
`build_viz.py`.

**Tie-out.** Nation and states, 2015 and 2025, match data.census.gov cell
for cell (`tieout.py`, section 4).

## R-CPI-U-RS (Bureau of Labor Statistics)

**What it is.** The Consumer Price Index research series using current
methods, all items, U.S. city average, annual averages. The ACS general
handbook (2020), chapter 10, says the Census Bureau recommends factors based
on the all-items CPI-U-RS when comparing ACS dollar figures across years.

**File.** `data/raw/cpi/r-cpi-u-rs-allitems.xlsx`, from
https://www.bls.gov/cpi/research-series/r-cpi-u-rs-allitems.xlsx. 2015: 348.3
(the file's AVG). BLS notes that October 2025 was not collected during the 2025
lapse in appropriations. The file's 2025 AVG cell (474.994) is not the mean of
its 11 published months (474.682), and BLS does not say how it was made. We
use the 11-month mean, which matches how BLS describes 2025 CPI annual
averages in its shutdown FAQ
(https://www.bls.gov/cpi/additional-resources/2025-federal-government-shutdown-impact-cpi-faq.htm).

**Use here.** 2015 medians times 474.682 / 348.3 (prices up 36.3%) to put
them in 2025 dollars. For the student debt charts, 2016 dollars (debt from
the Survey of Consumer Finances and B20004 medians) are multiplied by
474.682 / 352.8 (prices up 34.5%).

## Survey of Consumer Finances, 2016 and 2025 (Federal Reserve Board)

**What it is.** A survey of several thousand families every three years
on their assets, debts and income. 2016 is the survey year closest to 2015,
and 2025 is the latest. It is national only, so student debt is shown in
static national charts, not on the map.

**Files.** Full public data and replicate weights (Stata), codebooks, the
summary-variable macros (`bulletin.macro.txt`), the 2025 questionnaire
changes and the standard error documentation, from
https://www.federalreserve.gov/econres/scfindex.htm. `scripts/fetch_scf.py`
downloads them to `data/raw/scf/`. The data files are not committed. Sample:
6,248 families in 2016 and 4,360 in 2025, each with five implicates.

**Fields.**
- Highest degree: X5931 (reference person), X6111 (spouse or partner).
  Groups: less than high school (codes −1 and 1 to 7), high school or equivalent
  (8), some college or associate's (9 to 11), bachelor's (12), master's (13),
  professional or doctorate (14; the public data combine doctorate, code 15,
  with 14). Graduate or professional is 13 and 14.
- Age: X14 (reference person), X19 (spouse or partner).
- Student loans: for each of up to six loans, the amount still owed (X7824,
  X7847, X7870, X7924, X7947, X7970) and whose education it paid for (X7978,
  X7883, X7888, X7893, X7898, X7993: 1 reference person, 2 spouse or partner,
  3 child or other relative; the 2025 questionnaire adds 6, multiple people,
  but that code does not occur in the 2025 public data). X7179 is the
  total still owed on a family's seventh and later loans.
- Weights: X42001. Replicate weights WT1B1 to WT1B999 times the multiplicity
  factors MM1 to MM999; a missing replicate weight (a case not drawn in that
  replicate) counts as zero.

**Method.**
- Each family's reference person and, where present, spouse or partner is a
  person, ages 25 and over. A partner who is not part of the family unit
  (X100 = 5, degree code 0) was not interviewed and is left out. A person's own student debt is the sum still owed
  on loans for their own education. Loans for a child or other relative,
  loans for multiple people, and seventh and later loans are not assigned,
  because the 2016 survey did not ask whose education the seventh and later
  loans paid for.
- Measures by highest degree: percent with own student debt; median and mean
  own debt among those with debt; mean own debt per adult.
- Estimates are the average over the five implicates. Standard errors follow
  the SCF codebook's MEANIT macro: sqrt(6/5 × imputation variance + replicate
  variance), with imputation variance across the five implicates (n − 1
  divisor) and replicate variance across the 999 replicates of the first
  implicate (998 divisor). MOE = 1.645 × SE. A 2016-to-2025 change passes if
  |difference| / sqrt(SE₁² + SE₂²) > 1.645.
- Dollars are in 2025 dollars using the R-CPI-U-RS (above).

**Checks.** For every family, the sum of loans 1 to 6 plus X7179 equals the
Fed's summary variable EDN_INST in the 2025 summary extract. In 2016 it equals
EDN_INST divided by 1.3498, the Fed's factor for putting 2016 dollars in 2025
dollars, and the percent of families with education debt is the same (22.27%
in 2016, 19.92% in 2025).

**Caveats.**
- The share of all student loan balances assigned to a person is 84.4% in
  2016 and 85.6% in 2025; most of the rest is loans for a child or other
  relative.
- Loans of adults who are not the reference person or spouse, such as adult
  children living with parents, are not in the family's answers.
- The SCF total for student debt ($1.15 trillion in 2025) is below totals
  from credit reports, so the survey may miss some borrowers.
- In 2025 the survey changed the student loan question to exclude loans that
  someone outside the household is repaying, added the "multiple people"
  code, and changed who counts as a spouse or partner in the family. These
  could move the 2016-to-2025 comparison. We cannot measure by how much.
- Debt amounts bunch at round numbers (for example $25,000), so the replicate
  standard errors of medians can be very small or zero. The tests of median
  changes may overstate precision. The tests on percent with debt and on
  means do not have this problem.
- Samples are small for some groups: in 2025, 48 professional or doctorate
  borrowers and 5 borrowers with less than high school. For less than high
  school, some replicates have no borrowers at all (3 of 999 at ages 25 and
  over, 247 at ages 25 to 39), so its standard errors and tests are not
  reliable and are not used.

## Student debt from credit reports (New York Fed Consumer Credit Panel / Equifax)

**What it is.** A 5% sample of U.S. credit reports. Student loans include
federal and private loans. Balances are at year end, and state is the
borrower's mailing address, not the school's location. Credit reports do not
record education, so this source has no breakdown by degree.

**Files.** From the New York Fed Center for Microeconomic Data data bank
(https://www.newyorkfed.org/microeconomics/databank.html), saved in
`data/raw/nyfed/`:
- `student-loan-update-2025-mangrum.xlsx` (2024 Student Loan Debt
  Statistics): Page 8, national median and average balance per borrower,
  2004 to 2024; Pages 9 to 14, borrowers and average and median balance by
  state, 2019Q4 to 2024Q4.
- `student-loan-by-state.xlsx`: borrowers and average balance per borrower by
  state, 2016 to 2021. Its 2019 to 2021 averages match the update file to
  within 0.5% (checked in `scripts/credit_debt.py`), so 2016 state averages
  come from this file.
- `area_report_by_year.xlsx` and `hhd_c_report_2026q2.xlsx` were downloaded
  for reference and are not used.

**Method.** Average balance per borrower by state, 2016 and 2024, and the
national median and average per borrower, 2004 to 2024, moved to 2025
dollars with the R-CPI-U-RS. The update file has no United States row; the
national average from Page 8 is used, which matches the older file's United
States row for 2016. 2016 is the first year with state averages per borrower,
and 2024 is the latest. The New York Fed publishes no margins of error for
these tables, so no changes are tested.

**Caveats.**
- Puerto Rico's 2016 value comes from the older file and its change (+20.8%)
  is far from every state's; we have not confirmed it.
- Balances of borrowers who move count in the state where they live at year
  end.

## Cartographic boundary files, 2023 (Census Bureau)

**What it is.** Generalized outlines of states, counties and metro and micro
areas at 1:20,000,000 scale: `cb_2023_us_state_20m.zip`,
`cb_2023_us_county_20m.zip` and `cb_2023_us_cbsa_20m.zip`, from
https://www2.census.gov/geo/tiger/GENZ2023/shp/, saved in
`data/raw/boundaries/`.

**Why 2023.** The 2025 ACS uses Connecticut's planning regions as counties and
the July 2023 OMB metro and micro definitions; the 2023 files have both.

**Use here.** Drawing the map only. `scripts/build_geo.py` projects them
(Albers equal-area, with Alaska, Hawaii and Puerto Rico moved into insets),
simplifies the outlines to 0.3 pixels, and writes `data/clean/geo_paths.json`
(50 states, DC and Puerto Rico, 3,216 counties, 935 metro and micro areas). Every
area with a 2025 value at those three levels has a matching shape.

## Geography

Levels used, by GEOID (the `GEO_ID` field, which includes the summary-level
prefix, so codes never collide across levels; metro areas by CBSA code, see
above):

| Level | Why |
|---|---|
| Nation | asked for |
| Census region, division | added: boundaries never change, and they give context for the states |
| State + DC | asked for |
| Puerto Rico | published at state level; kept apart, not in the national total |
| County | asked for |
| Metro and micro area | asked for |
| Place | asked for |

Other levels the 1-year files publish, and why we leave them out:

| Level | Reason |
|---|---|
| Congressional district | redrawn after each census and sometimes mid-decade |
| PUMA | redrawn in 2012 and 2022 |
| Urban area | redefined after the 2020 Census |
| School districts | boundaries updated every year |
| Combined statistical area, metro division | redefined with each metro delineation |
| County subdivision, principal city | mostly repeat places, and principal cities follow metro definitions |
| American Indian / Alaska Native areas | few cross 65,000; worth a separate look |

**The 65,000 threshold and the every-year panel.** The ranked view uses only
areas with values in every year of the series (2008–2019, 2021–2025). Every
other area is listed in `data/clean/areas.csv` with the reason its series is
broken: first year published, last year published, years missing (below the
threshold), years withheld, name change.

**Metro boundary changes.** We compared each metro area's list of counties
across the OMB delineation files each ACS year used (saved in
`data/raw/delineations/`, from
`https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/`).
146 of the 457 every-year metro areas changed counties at least once (first
used in 2013, 2016, 2019 or 2023). Some changes are large: Salisbury, MD-DE's
population 25 and over rose 230% in 2013 when it added counties. We drop from
the ranked view any metro area whose population 25 and over moved 5% or more
from the prior published year in a year its own county makeup changed (111
metro areas), which leaves 346. A jump in that year is not proof the boundary
caused it: 81 metro areas with no county change also moved 5% or more in a
delineation year (often 2010 or 2021). Bedford County, Virginia, is dropped by
the same rule (its adult population rose 11% from 2013 to 2014, when it took in
Bedford city). The rest keep a note
naming the years their makeup changed. Details are in
`data/clean/cbsa_changes.csv`. The 5% cut is our choice, not a Census rule.

## Method

**Comparable basis.** For 2008–2024, "Less than grade 1" = No schooling
completed + Nursery school + Kindergarten. 2025 uses the published "Less than
grade 1" line. This detail line is built for checking only.

**The five groups** (shares of the population 25 and over):

| Group | B15003 lines (by label) |
|---|---|
| Less than high school | No schooling, Nursery, Kindergarten (or Less than grade 1), 1st through 11th grade, 12th grade no diploma |
| High school or equivalent | Regular high school diploma, GED or alternative credential |
| Some college or associate's | Some college less than 1 year, Some college 1 or more years no degree, Associate's degree |
| Bachelor's | Bachelor's degree |
| Graduate or professional | Master's, Professional school, Doctorate |

**Margins of error.** From the Census Bureau's *Understanding and Using
American Community Survey Data: What All Data Users Need to Know* (2020),
https://www.census.gov/programs-surveys/acs/library/handbooks/general.html:

- Sum of lines (chapter 8, formula 1): MOE = √(MOE₁² + MOE₂² + … + MOEₙ²).
- Share (chapter 8, formula 6): with p = X / Y,
  MOE(p) = (1/Y) √(MOE(X)² − p² · MOE(Y)²). If the value under the root is
  negative, the handbook says to use a plus sign instead (formula 7).
- Standard error (chapter 7, formula 1): SE = MOE / 1.645.
- Change over time (chapter 7, formula 3): z = (p₂ − p₁) / √(SE₁² + SE₂²). A
  change is called real only if |z| > 1.645 (90% confidence).

The handbook warns that these formulas leave out the correlation between lines,
and that the error grows as more lines are added up. The S1501 tie-out shows
our share MOEs within about 10% to 20% of the direct ones. The handbook's own
testing tool makes no correction for many comparisons, and neither do we. The
every-year panel has 8,940 tests across states, counties, metro areas and places;
if nothing had changed anywhere, about 894 would pass by chance. Far more than
that pass (see FINDINGS.md), but any single small change that passes could
still be chance.

**Map** (`dist/index.html`). Shows states, counties and metro and micro
areas, with five measures built from the groups: bachelor's or more
(bachelor's + graduate), graduate or professional, some college or more, high
school or more, and less than high school. Sums use formula 1 and shares use
formula 6 or 7, computed in the page from the embedded counts and MOEs.

- *Share in 2025* view: six color classes with about equal numbers of areas,
  rounded to whole percents and computed for each level and measure, in
  blue. Gray
  means no 2025 1-year estimate; none of the gray areas were published with
  empty tables in 2025.
- *Change, 2015 to 2025* view: a decade, in percentage points. Only changes
  that pass the z-test (formula 3) are colored; the rest are hatched. Rises
  are blue and falls orange, except for less than high school, where falls
  are blue and rises orange. Classes
  are symmetric around zero in steps of k and 2k points, where k is the round
  number (0.5, 1, 1.5, 2, 2.5, 3, 4 or 5) closest to a third of the 90th
  percentile of the size of the changes that pass, for each level and measure.
- A 2015 value and change are shown only for areas published in every year
  from 2015 to 2025, and for metro and micro areas only where no county-makeup
  change that took effect after 2015 (first used in 2016, 2018, 2019, 2021 or
  2023) moved the population 25 and over by 5% or more from the prior
  published year. Bedford County, Virginia's 2013 change is before the window,
  so it is compared.
- Because 2025 is a break year for the three measures that include less than
  high school or some college, the page notes how far each moved beyond its
  2021–2024 trend nationally.

**Pay views of the map.** Same areas and the same 2015 comparability rule as
the education views.

- Median pay in 2025, and its yearly change from 2015, for all workers and
  for each of the five groups. Yearly change is the compound annual growth
  rate, ((2025 value / 2015 value in 2025 dollars)^(1/10) − 1). The test is
  formula 3 on the dollar change, with 2015 MOEs scaled by the same price
  factor.
- Pay index growth from the change in pay within education groups (education
  mix held at 2015): index = Σ w₂₀₁₅,g × median_g, where w is the
  area's B15003 share of adults 25 and over in group g. MOE of the index uses
  formula 1 on w × MOE, with weights treated as fixed; the 2015-to-2025 test
  uses the ratio MOE (formula 7) and asks whether the ratio differs from 1.
- Pay index growth from the change in education mix: yearly growth of the index with each year's own
  weights, minus yearly growth with 2015 weights. It is not a share of median
  pay growth.
- Approximate tests for the education mix part and the pay index total (shown
  on hover). Neither has a published Census formula, so each is built from
  the handbook's pieces. The mix part has the sign of
  D = Σ (q₂₀₂₅,g − q₂₀₁₅,g) × median₂₀₂₅,g, and the total is
  T = Σ q₂₀₂₅,g × median₂₀₂₅,g − Σ q₂₀₁₅,g × median₂₀₁₅,g (2015 in 2025 dollars),
  where q is the group's share of adults 25 and over. The standard error adds,
  by root-sum-of-squares: each share's SE (formula 6, MOE/1.645) times
  (median_g − Σ q × median, using that term's shares and the same
  medians), and each median's SE times its
  share (or, for D, times the change in share). Using median minus index
  allows for the five shares adding to 100%, so an error in one share is
  offset in the others. Shares and medians are treated as independent,
  although they come from the same survey. A test passes if |D| or |T| is more
  than 1.645 times its SE.
- Change classes use the same symmetric k and 2k rule, with k from {0.1, 0.2,
  0.25, 0.5, 0.75, 1, 1.5, 2}% a year (or {0.05, 0.1, 0.2, 0.25, 0.5, 0.75, 1}
  points a year for the mix part). Level classes are equal-count, rounded to
  $1,000.

**Names.** Each area carries its name in the latest year it was published.

**Build order.** `fetch.py` → `build.py` → `geo_flags.py` → `findings.py` →
`build_geo.py` → `build_viz.py` → `pay_findings.py`; `tieout.py` checks against data.census.gov.

## Variable mapping

B15003, by label. "—" means the line does not exist that year.

| Label | Group | Line number by year |
|---|---|---|
| Total | Total | 2008–2025: 001 |
| No schooling completed (less than grade 1 detail) | Less than high school | 2008–2024: 002; 2025: — |
| Nursery school (less than grade 1 detail) | Less than high school | 2008–2024: 003; 2025: — |
| Kindergarten (less than grade 1 detail) | Less than high school | 2008–2024: 004; 2025: — |
| Less than grade 1 (less than grade 1 detail) | Less than high school | 2008–2024: —; 2025: 002 |
| 1st grade | Less than high school | 2008–2024: 005; 2025: 003 |
| 2nd grade | Less than high school | 2008–2024: 006; 2025: 004 |
| 3rd grade | Less than high school | 2008–2024: 007; 2025: 005 |
| 4th grade | Less than high school | 2008–2024: 008; 2025: 006 |
| 5th grade | Less than high school | 2008–2024: 009; 2025: 007 |
| 6th grade | Less than high school | 2008–2024: 010; 2025: 008 |
| 7th grade | Less than high school | 2008–2024: 011; 2025: 009 |
| 8th grade | Less than high school | 2008–2024: 012; 2025: 010 |
| 9th grade | Less than high school | 2008–2024: 013; 2025: 011 |
| 10th grade | Less than high school | 2008–2024: 014; 2025: 012 |
| 11th grade | Less than high school | 2008–2024: 015; 2025: 013 |
| 12th grade, no diploma | Less than high school | 2008–2024: 016; 2025: 014 |
| Regular high school diploma | High school or equivalent | 2008–2024: 017; 2025: 015 |
| GED or alternative credential | High school or equivalent | 2008–2024: 018; 2025: 016 |
| Some college, less than 1 year | Some college or associate's | 2008–2024: 019; 2025: 017 |
| Some college, 1 or more years, no degree | Some college or associate's | 2008–2024: 020; 2025: 018 |
| Associate's degree | Some college or associate's | 2008–2024: 021; 2025: 019 |
| Bachelor's degree | Bachelor's | 2008–2024: 022; 2025: 020 |
| Master's degree | Graduate or professional | 2008–2024: 023; 2025: 021 |
| Professional school degree | Graduate or professional | 2008–2024: 024; 2025: 022 |
| Doctorate degree | Graduate or professional | 2008–2024: 025; 2025: 023 |
