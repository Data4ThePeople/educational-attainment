"""Tie-out: national and state numbers against data.census.gov.

For 2019, 2023 and 2025, nation and every state (plus DC and Puerto Rico):
  1. Every B15003 line, estimate and MOE, from data.census.gov's table service
     vs the Census API pull saved in data/raw/.
  2. The five group counts and the table total, rebuilt from the
     data.census.gov lines, vs data/clean/panel.csv.
  3. Our five shares vs the Census Bureau's own percentages in subject table
     S1501 (also from data.census.gov), and our approximated share MOEs vs
     S1501's directly computed MOEs.

Writes data/clean/tieout_report.md and exits non-zero on any mismatch in 1 or 2.
"""
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent))
from mapping import GROUPS, GROUP_NAMES, RAW, ROOT, B15003_MAP  # noqa: E402

YEARS = [2019, 2023, 2025]
DCG = "https://data.census.gov/api/access/data/table"
GEOS = ["010XX00US", "010XX00US$0400000"]
OUT = ROOT / "data" / "clean" / "tieout_report.md"
CACHE = ROOT / "data" / "raw" / "tieout"


def dcg(table_id):
    """All rows for the nation and states from data.census.gov, cached as-is."""
    rows, header = [], None
    for g in GEOS:
        path = CACHE / f"{table_id}_{re.sub(r'[^0-9A-Za-z]', '_', g)}.json"
        if not path.exists():
            # The service sometimes returns an empty 200; retry, never cache one.
            for i in range(5):
                r = requests.get(DCG, params={"id": table_id, "g": g}, timeout=120)
                r.raise_for_status()
                if r.text.strip():
                    break
                time.sleep(5 * (i + 1))
            else:
                raise RuntimeError(f"data.census.gov returned no data for {table_id} {g}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(r.text)
        d = json.loads(path.read_text())["response"]["data"]
        header = header or d[0]
        rows += [dict(zip(d[0], r)) for r in d[1:]]
    return pd.DataFrame(rows)


def api_rows(year):
    out = []
    for level in ("us", "state"):
        js = json.loads((RAW / str(year) / f"B15003_{level}.json").read_text())
        out += [dict(zip(js[0], r)) for r in js[1:]]
    return pd.DataFrame(out)


def labels(year, table, sub=""):
    v = json.loads((RAW / str(year) / f"variables_{table}.json").read_text())["variables"]
    return {k: v[k]["label"] for k in v}


def leaf(label):
    return re.sub(r":$", "", label.split("!!")[-1]).strip().lower()


def check_lines(year, report):
    web = dcg(f"ACSDT1Y{year}.B15003").set_index("GEO_ID")
    api = api_rows(year).set_index("GEO_ID")
    cols = [c for c in api.columns if re.fullmatch(r"B15003_\d{3}[EM]", c)]
    missing_geo = sorted(set(api.index) ^ set(web.index))
    diffs = []
    for gid in api.index.intersection(web.index):
        for c in cols:
            a, w = api.at[gid, c], web.at[gid, c] if c in web.columns else None
            if str(a) != str(w):
                diffs.append((gid, c, a, w))
    report.append(f"- {year}: {len(api)} API rows, {len(web)} data.census.gov rows, "
                  f"{len(cols)} columns each, {len(diffs)} differing cells, "
                  f"{len(missing_geo)} areas in one source only")
    for d in diffs[:20]:
        report.append(f"  - {d}")
    return web, len(diffs) + len(missing_geo)


def check_panel(year, web, panel, report):
    lab = labels(year, "B15003")
    group_of = {}
    for var, L in lab.items():
        if re.fullmatch(r"B15003_\d{3}E", var):
            key = leaf(L)
            group_of[var] = "total" if key == "total" else B15003_MAP[key][0]
    p = panel[panel.year == year].set_index("geoid")
    bad = 0
    for gid, row in web.iterrows():
        sums = {}
        for var, g in group_of.items():
            sums[g] = sums.get(g, 0) + int(row[var])
        for g, v in sums.items():
            if gid not in p.index or int(round(p.at[gid, f"{g}_est"])) != v:
                bad += 1
                report.append(f"  - {year} {gid} {g}: data.census.gov {v}, panel "
                              f"{p.at[gid, f'{g}_est'] if gid in p.index else 'missing'}")
    report.append(f"- {year}: group counts and totals for {len(web)} areas, {bad} mismatches")
    return bad


S1501_LEAVES = {
    "less than 9th grade": "lths",
    "9th to 12th grade, no diploma": "lths",
    "high school graduate (includes equivalency)": "hs",
    "some college, no degree": "somecol",
    "associate's degree": "somecol",
    "bachelor's degree": "ba",
    "graduate or professional degree": "grad",
}


def check_s1501(year, panel, report):
    web = dcg(f"ACSST1Y{year}.S1501").set_index("GEO_ID")
    lab = labels(year, "S1501")
    pct_vars = {}
    for var, L in lab.items():
        if not re.fullmatch(r"S1501_C\d\d_\d{3}E", var):
            continue
        parts = [x.rstrip(":").strip().lower() for x in L.split("!!")]
        if "percent" not in parts[1] or "population 25 years and over" not in parts:
            continue
        if parts[-2] != "population 25 years and over" or parts[1] != "percent":
            continue
        if parts[-1] in S1501_LEAVES and "male" not in parts[1] and "female" not in parts[1]:
            pct_vars[var] = S1501_LEAVES[parts[-1]]
    if len(pct_vars) != 7:
        report.append(f"- {year}: could not find the 7 S1501 percent lines (found {pct_vars}); skipped")
        return
    p = panel[panel.year == year].set_index("geoid")
    rows = []
    for gid, row in web.iterrows():
        pub = {}
        for var, g in pct_vars.items():
            e, m = float(row[var]), float(row[var[:-1] + "M"])
            pe, pm2 = pub.get(g, (0.0, 0.0))
            pub[g] = (pe + e, pm2 + m * m)
        for g in GROUPS:
            rows.append({"geoid": gid, "group": g, "s1501": pub[g][0],
                         "ours": p.at[gid, f"{g}_share"],
                         "s1501_moe": np.sqrt(pub[g][1]) if g in ("lths", "somecol") else np.sqrt(pub[g][1]),
                         "moe_is_derived": g in ("lths", "somecol"),
                         "ours_moe": p.at[gid, f"{g}_share_moe"]})
    df = pd.DataFrame(rows)
    df["diff"] = df.ours - df.s1501
    # S1501 percents are rounded to 0.1; a two-line sum can be off by 0.1.
    tol = np.where(df.moe_is_derived, 0.1 + 1e-9, 0.05 + 1e-9)
    off = df[df["diff"].abs() > tol]
    report.append(f"- {year}: {len(df)} share comparisons, {len(off)} outside rounding "
                  f"(max abs diff {df['diff'].abs().max():.3f} points)")
    for _, r in off.head(10).iterrows():
        report.append(f"  - {r.geoid} {r.group}: ours {r.ours:.2f}, S1501 {r.s1501:.1f}")
    single = df[~df.moe_is_derived & (df.s1501_moe > 0)]
    ratio = (single.ours_moe / single.s1501_moe)
    report.append(f"  - share MOE, ours / S1501 direct, groups that are one line in S1501 (HS, bachelor's, graduate): "
                  f"median {ratio.median():.2f}, 10th pct {ratio.quantile(.1):.2f}, 90th pct {ratio.quantile(.9):.2f}")
    return df


CLAIMS = [
    # (text that must appear on the page, status, source)
    ("Educational attainment of adults 25 and over, 2008 to 2025", "supported",
     "B15003 universe is the population 25 and over; series runs 2008-2025 (DATASETS.md)"),
    ("for the nation, regions, divisions, states, Puerto Rico, and the counties, metro and micro areas and places with 65,000 or more people", "supported",
     "ACS 1-year publication threshold (user note 2026-06); levels pulled (DATASETS.md, Geography)"),
    ("the three lowest answers are added together to match the 2025 question", "supported",
     "user note 2026-02; mapping in DATASETS.md"),
    ("No standard 1-year estimates were released for 2020", "supported",
     "user note 2021-02, https://www.census.gov/programs-surveys/acs/technical-documentation/user-notes/2021-02.html"),
    ("B15002 fills years where B15003 was published with no values", "supported",
     "build.py fill_withheld; 851 area-years, exact match where both exist (findings_tables.md)"),
    ("Bands show the 90% margin of error, approximated with the Census Bureau's formulas for derived estimates", "supported",
     "ACS handbook (2020) ch. 8 formulas 1, 6, 7"),
    ("pass the Census Bureau's test at 90% confidence", "supported", "ACS handbook (2020) ch. 7 formula 3"),
    ("In ${LAST} the survey merged its three lowest answers into one, collected less data during a federal funding lapse, and used a new population base.",
     "supported", "user notes 2026-02, 2026-04, 2026-05"),
    ("percentage points more than its ${LAST - 4}–${LAST - 1} trend", "supported",
     "findings_tables.md: beyond-trend group changes; numbers recomputed below"),
    ("Changes ending in ${LAST} for this group include that step.", "supported",
     "states the arithmetic only, no cause"),
    ("it was under 65,000 people, or the tables were published with no values", "supported",
     "ACS 1-year threshold; null tables in the API (withheld.csv)"),
    ("Built by Data 4 The People", "supported", "house convention"),
]


def check_words(panel, report):
    html = (ROOT / "dist" / "index.html").read_text()
    for text, status, src in CLAIMS:
        found = text in html
        report.append(f"- \"{text}\": {status if found else 'NOT FOUND ON PAGE'} ({src})")
    us = panel[panel.level == "us"].set_index("year").lths_share
    sc = panel[panel.level == "us"].set_index("year").somecol_share
    excess = -((us[2025] - us[2024]) - (us[2024] - us[2021]) / 3)
    excess_sc = (sc[2025] - sc[2024]) - (sc[2024] - sc[2021]) / 3
    report.append(f"- Break note numbers, recomputed here: less than high school {excess:.1f}, some college "
                  f"{excess_sc:.1f} points (the page computes them the same way at load).")
    report.append("- Level names: \"Places (cities, towns and CDPs)\" covers census-designated places, "
                  "which are not cities; supported.")
    return sum(1 for t, _, _ in CLAIMS if t not in html)


def main():
    panel = pd.read_csv(ROOT / "data" / "clean" / "panel.csv")
    report = ["# Tie-out against data.census.gov", "",
              "## 1. B15003 lines: Census API pull vs data.census.gov", ""]
    fails = 0
    webs = {}
    for y in YEARS:
        webs[y], n = check_lines(y, report)
        fails += n
    report += ["", "## 2. Group counts and totals: panel.csv vs data.census.gov lines", ""]
    for y in YEARS:
        fails += check_panel(y, webs[y], panel, report)
    report += ["", "## 3. Shares vs S1501 published percentages", ""]
    for y in YEARS:
        check_s1501(y, panel, report)
    report += ["", "## 4. Words on the built page (dist/index.html)", ""]
    fails += check_words(panel, report)
    report += ["", f"**Result:** {'PASS' if fails == 0 else f'FAIL ({fails} problems)'} on sections 1, 2 and 4."]
    OUT.write_text("\n".join(report) + "\n")
    print("\n".join(report))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
