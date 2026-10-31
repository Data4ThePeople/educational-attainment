# Findings, Step 1

All numbers come from `data/clean/findings_tables.md` (written by
`scripts/findings.py`). "Significant" means the change passes the Census
Bureau's test at 90% confidence. Shares are of adults 25 and over. Changes are
in percentage points, 2008 to 2025, for areas with values in every year.

## Biggest changes

1. **Nation.** From 2008 to 2025, the share with less than high school fell
   from 15.0% to 9.4%. Bachelor's rose from 17.5% to 22.3%, and graduate or
   professional from 10.2% to 15.0%. High school or equivalent fell from 28.5%
   to 25.6%, and some college or associate's from 28.8% to 27.7%. All five
   changes are significant.
2. **Every region and division** shows the same five directions, with one
   exception: some college rose in the East South Central division (28.1% to
   29.3%).
3. **States.** All 50 states and DC had significant rises in bachelor's and in
   graduate shares, and significant falls in less than high school.
   - Largest falls in less than high school: Kentucky (18.7% to 9.9%), Arkansas
     (18.0% to 9.3%), Mississippi (20.1% to 11.7%), Texas (20.4% to 12.2%) and
     West Virginia (17.8% to 9.7%).
   - Largest bachelor's rises: Maine (16.5% to 23.8%), South Carolina (15.2% to
     21.6%) and North Carolina (17.4% to 23.3%).
   - Largest graduate rises: DC (26.7% to 38.7%), Vermont (12.3% to 20.1%) and
     Massachusetts (16.4% to 23.2%).
4. **Counties, metro areas and places** follow the national pattern. Of 782
   every-year counties, 664 had a significant fall in less than high school,
   and one had a rise (Rockland County, NY, below).

## Places that stand out

- **Sumter County, FL** had the largest bachelor's rise of any county (7.6% to
  23.3%). Its graduate share rose from 3.0% to 14.9%, and less than high school
  fell from 17.8% to 5.0%.
- **Rockland County, NY** is the only every-year county where less than high
  school rose significantly (10.4% to 12.8%; it just clears the test). Its
  less-than-grade-1 share rose from 1.0% in 2008 to 4.3% in 2024.
- **Silicon Valley places** had the largest graduate rises: Milpitas (12.4% to
  34.2%), Santa Clara (21.6% to 39.8%), Mountain View (25.3% to 42.9%). San
  Jose-Sunnyvale-Santa Clara leads the metro areas (19.2% to 29.9%).
- **Largest falls in less than high school** among metro areas are in South
  Texas and New Mexico: McAllen-Edinburg-Mission (41.7% to 26.5%),
  Brownsville-Harlingen (36.8% to 21.5%) and Gallup, NM (36.7% to 16.9%).
  Among places: Pharr, TX (43.7% to 22.6%), Baldwin Park, CA (50.6% to 31.2%)
  and Miami, FL (33.4% to 14.5%). Puerto Rico's municipios and metro areas
  also had falls of 16 to 21 points.
- **Places where less than high school rose:** Plantation, FL (2.8% to 6.5%)
  and Bloomington, MN (4.9% to 8.5%). Plantation's 2008 value comes from
  B15002.
- **Places where the bachelor's share fell:** Iowa City, IA (31.2% to 23.0%),
  Lauderhill, FL (16.8% to 10.3%) and Hoover, AL (37.3% to 31.8%). Hoover's
  2008 value comes from B15002.

## Things that look like side effects of the method or the data

1. **The 2025 question change reaches past "less than high school."** This
   goes against the starting assumption. Less than grade 1 fell 1.40 points
   beyond its trend nationally. Only about 0.9 points of that shows up
   elsewhere in less than high school. Beyond trend, less than high school fell
   0.53 points and some college or associate's rose 0.55. High school (+0.09),
   bachelor's (−0.11) and graduate (0.00) moved little. In 2024 to 2025, 53% of
   states had a significant one-year change in less than high school, against
   12% to 37% in the earlier year pairs we checked. Across states, counties and
   metro areas, a bigger drop in less than grade 1 goes with a bigger unusual
   drop in less than high school. So 2008 to 2025 changes in those two groups
   may include part of the question change. The result holds for any trend
   base from 2008 to 2022. The viz dashes the 2024 to 2025 step
   for them and says so. Bachelor's, graduate and high school look clean.
2. **A 2021 step in the less-than-grade-1 line.** It rose from 1.51% in 2019
   to 2.00% in 2021 nationally, and rose significantly in 42 states, against
   2 to 15 states in other year pairs. The filled-in share also stepped up that
   year (7.9% to 9.8%) and in 2013 (5.1% to 7.1%), when less than grade 1 also
   rose in 15 states. These steps are in the detail line. They are small next
   to the five-group trends, but they are not a smooth series.
3. **Apache County, AZ.** Less than high school fell from 31.3% to 16.7% from
   2008 to 2024. Of that 14.6-point fall, 10.7 points (73%) is in the less
   than grade 1 line, the answer the Census Bureau says the old question
   over-counted. Redlands, CA is the only other every-year area where that
   line is most of a 2-point-plus fall (55%). These falls may partly reflect
   how people answered rather than real change.
4. **Filled-in answers rose over time.** About 10.2% of adults nationally had
   their attainment answer filled in by the Census Bureau in 2025, against
   4.6% in 2008. The tables don't separate measured from filled answers.
5. **Withheld tables.** B15003 was published with no values for 1,049
   area-years over the threshold, mostly places, more often in later years.
   851 are filled from B15002 (same counts where both exist); 198 are dropped.
6. **Metro boundaries.** 146 of 457 every-year metro areas changed counties
   with new OMB delineations. 111 had a change that moved their population 25
   and over by 5% or more in one year and are left out of the ranked view.
   That leaves 346. The 5% cut is ours, and a jump in that year is not proof
   the boundary caused it. Bedford County, VA is dropped by the same rule.
7. **Wider 2025 margins.** The median MOE of the bachelor's share rose 7% to
   11% from 2024 to 2025, depending on level. Tests that end in 2025 are a
   little harder to pass.
8. **Many tests.** The every-year panel has 8,940 tests across states, counties,
   metro areas and places. If nothing had changed, about 894 would pass by chance. Far more
   pass, but any one small change that passes could still be chance.
9. **Population controls.** Nationally the population 25 and over grew 1.05%
   from 2024 to 2025, inside the 2009–2024 range (0.66% to 1.78%). We see no
   jump in the count that points to the new control base, but shares could
   still move a little for that reason.

## Pay and the education mix, 2015 to 2025

Numbers in this section come from `data/clean/pay_tables.md` (written by
`scripts/pay_findings.py`). Pay is median earnings of people 25 and over who
had earnings, in 2025 dollars using the R-CPI-U-RS (2025 is the mean of the 11
published months). Yearly change is the compound annual growth rate over the
10 years. The pay index weights each education group's median pay by the
area's share of adults 25 and over in that group.

1. **Nationally, the pay index grew about half as fast with the education mix
   held at 2015.** Median pay for all workers rose 0.98% a year. The pay index
   rose 1.00% a year with each year's own education mix and 0.49% a year with
   the mix held at 2015. The difference, 0.51 points a year, is the pay index growth
   from the change in education mix.
2. **Within each group, median pay grew more slowly than the overall median,
   except for less than high school.** National yearly changes: less than high
   school 1.78%, high school 0.48%, some college or associate's 0.65%,
   bachelor's 0.33%, graduate or professional −0.02%.
3. **The pattern holds across areas.** Pay index growth from the change in
   education mix is above zero in 379 of 391 comparable metro and micro areas, 780 of 805
   counties, and all 50 states, DC and Puerto Rico. Its median is 0.39 points a
   year for metro and micro areas and 0.40 for counties. It has no
   significance test.
4. **Pay index growth from the change in pay within education groups (the
   2015-mix index) is smaller and less often significant.**
   In metro and micro areas, median pay for all workers rose significantly in
   227 of 391 and fell significantly in 1. The 2015-mix index rose
   significantly in 149 and fell significantly in 10.
5. **Areas that stand out.** The largest pay index growth from the change in
   education mix among metro and micro areas include Guayama, PR (1.09 points a year),
   Brownsville-Harlingen, TX (0.97) and San Jose-Sunnyvale-Santa Clara, CA
   (0.96). The 2015-mix index fell most in Minot, ND (−1.59% a year),
   Trenton-Princeton, NJ (−1.05%) and Muskogee, OK (−1.03%); Houston fell
   0.53% a year, while its median for all workers was close to flat (−0.10%).
   Jackson, MS covers about 8% different land in 2025 than in 2015 (see the
   independent tie-out), so its numbers need care.

Limits:
- The weights are shares of all adults 25 and over, not of workers, while the
  medians cover earners only. So the difference in item 3 is not a share of
  median pay growth. Retirees are a larger share of adults with less
  schooling, so the index puts more weight on lower-paid groups than a
  worker-weighted index would. Census does not publish workers by all five
  groups (B23006 combines bachelor's and graduate degrees).
- A weighted average of medians is an index, not a median. Nationally the
  own-mix index (1.00% a year) is close to the median (0.98%). Across areas
  the two differ by −0.55 to +0.53 points a year (10th to 90th percentile,
  from the independent tie-out).
- The 2025 education mix includes the 2025 question change. Nationally less
  than high school fell 0.53 points more than trend, which raises the 2025
  own-mix index slightly.
- B20004 covers part-time and part-year workers, so changes in hours worked
  are part of these pay changes.
- Each yearly change uses only the 2015 and 2025 estimates, and 2025 was
  collected with less data during the funding lapse.

## Could not check

- Which metro delineation the 2008 ACS used (we assume November 2007).
- Place annexations: we do not track them.
- Whether the 2025 shift in less than high school comes from the question
  change, the collection lapse or the new controls. The cross-area pattern
  ties it to the question change, but the three cannot be fully separated with
  published tables.
