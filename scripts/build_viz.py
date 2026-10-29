"""Write the two pages, each with the panel's published counts and MOEs
embedded. The pages compute every share, MOE and test themselves.

  dist/index.html  viz/map_template.html: map by state, county or metro and
                   micro area of 2025 shares or of the change since 2015. Shapes from data/clean/geo_paths.json (build_geo.py).
  dist/lines.html  viz/template.html: 2008-2025 lines for any area, plus the
                   ranked view of changes.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from mapping import GROUPS, GROUP_NAMES, ROOT  # noqa: E402

CLEAN = ROOT / "data" / "clean"
LEVEL_ORDER = ["us", "region", "division", "state", "pr", "cbsa", "county", "place"]
LEVEL_NAMES = {"us": "Nation", "region": "Regions", "division": "Divisions", "state": "States",
               "pr": "Puerto Rico", "cbsa": "Metro and micro areas", "county": "Counties",
               "place": "Places (cities, towns and CDPs)"}
# Groups whose 2025 values carry part of the question change (FINDINGS.md, check 2).
BREAK_2025 = ["lths", "somecol"]


def years_phrase(years):
    n = len(str(years).split(", "))
    return ("the year " if n == 1 else "the years ") + str(years)


def flag_text(gid, r, flags):
    parts = []
    if not r["balanced"]:
        parts.append(f"Has values in {r['n_years']} of the 17 years ({r['first']}–{r['last']}), "
                     "so it is left out of the ranked view.")
    if r["b15002_years"]:
        parts.append(f"Values for {years_phrase(r['b15002_years'])} come from table B15002, because "
                     "B15003 was published with no values.")
    if r["withheld_years"]:
        parts.append(f"Both tables were published with no values in {r['withheld_years']}.")
    extra = flags.get(gid)
    if isinstance(extra, str) and extra:
        parts.append(extra)
    return " ".join(parts)


def main():
    p = pd.read_csv(CLEAN / "panel.csv")
    areas = pd.read_csv(CLEAN / "areas.csv").set_index("geoid").fillna({"b15002_years": "", "withheld_years": ""})
    flags_path = CLEAN / "geo_flags.csv"
    flags = pd.read_csv(flags_path).set_index("geoid").note.to_dict() if flags_path.exists() else {}
    # Metro areas whose county makeup changed enough to move their population
    # 25+ by 5% or more in a switch year leave the ranked view (findings.py).
    big = set(pd.read_csv(CLEAN / "cbsa_big_changes.csv").geoid)
    # Bedford County, VA took in Bedford city in 2013; its adult population
    # rose 11% from 2013 to 2014, so the same 5% rule applies.
    big.add("0500000US51019")
    cols = ["total_est", "total_moe"] + [f"{g}_{k}" for g in GROUPS for k in ("est", "moe")]
    out = []
    for gid, g in p.groupby("geoid", sort=False):
        a = areas.loc[gid]
        y = {int(r.year): [int(round(v)) for v in r[cols]] for _, r in g.iterrows()}
        # areas.csv carries the latest published name (older years show "?"
        # in place of accented letters).
        f = flag_text(gid, a, flags)
        if gid in big and a.balanced:
            f += (" Its adult population moved 5% or more in the year its boundary changed, "
                  "so it is left out of the ranked view.")
        out.append({"id": gid, "n": a["name"], "l": a.level, "b": bool(a.balanced) and gid not in big,
                    "f": f.strip(), "y": y})
    data = {
        "years": sorted(int(y) for y in p.year.unique()),
        "groups": [{"key": g, "name": GROUP_NAMES[g]} for g in GROUPS],
        "break2025": BREAK_2025,
        "levelOrder": LEVEL_ORDER,
        "levelNames": LEVEL_NAMES,
        "defaultId": "0100000US",
        "areas": out,
    }
    html = (ROOT / "viz" / "template.html").read_text()
    assert "/*DATA*/null" in html
    html = html.replace("/*DATA*/null", json.dumps(data, separators=(",", ":")))
    (ROOT / "dist").mkdir(exist_ok=True)
    (ROOT / "dist" / "lines.html").write_text(html)
    print(f"dist/lines.html: {len(out)} areas, {len(html) / 1e6:.1f} MB")
    build_map(out, areas, big)


# The map compares the latest year with this one: a decade.
MAP_BASE = 2015


def build_map(lines_areas, area_info, big):
    """The map shows the latest year and the change since MAP_BASE. A change is
    shown only for areas published in every year from MAP_BASE on, and, for
    metro and micro areas, only where no county-makeup change that took effect
    after MAP_BASE moved the population 25 and over by 5% or more from the
    prior published year (the ranked view's rule, applied to this window)."""
    geo = json.loads((CLEAN / "geo_paths.json").read_text())
    years = sorted({y for a in lines_areas for y in a["y"]})
    base, last = MAP_BASE, years[-1]
    window = [y for y in years if y >= base]
    # Population 25+ jumps in each metro's switch years inside the window.
    cc = pd.read_csv(CLEAN / "cbsa_changes.csv")
    tot = {a["id"]: {y: r[0] for y, r in a["y"].items()} for a in lines_areas if a["l"] == "cbsa"}
    jump = set()
    for gid, y in zip(cc.geoid, cc.first_year_new):
        t = tot.get(gid, {})
        prev = [v for v in t if v < y]
        if y > base and y in t and prev and abs(t[y] / t[max(prev)] - 1) >= 0.05:
            jump.add(gid)
    on_map = {f["id"] for lvl in ("state", "county", "cbsa") for f in geo[lvl]}
    areas = []
    for a in lines_areas:
        if a["id"] not in on_map or last not in a["y"]:
            continue
        every = all(y in a["y"] for y in window)
        rec = {"id": a["id"], "n": a["n"], "c": every and a["id"] not in jump,
               "v": {y: a["y"][y] for y in (base, last) if y in a["y"]}}
        if not rec["c"]:
            if not every:
                why = f"It was not published in every year from {base} to {last}, so no change since {base} is shown."
            else:
                why = (f"Changes to the counties in it moved its adult population by 5% or more in one year "
                       f"after {base}, so no change since {base} is shown.")
            if a["id"].startswith("0500000US09"):
                why += " Connecticut replaced its counties with planning regions in 2022."
            rec["why"] = why
        areas.append(rec)
    us = next(a for a in lines_areas if a["id"] == "0100000US")
    data = {"groups": GROUPS, "first": base, "last": last, "us": us["y"], "areas": areas}
    html = (ROOT / "viz" / "map_template.html").read_text()
    for k, v in (("DATA", data), ("GEO", geo)):
        assert f"/*{k}*/null" in html
        html = html.replace(f"/*{k}*/null", json.dumps(v, separators=(",", ":")))
    (ROOT / "dist" / "index.html").write_text(html)
    ids = {x["id"]: x["c"] for x in areas}
    by = {lvl: (sum(f["id"] in ids for f in geo[lvl]), sum(ids.get(f["id"], False) for f in geo[lvl]))
          for lvl in ("state", "county", "cbsa")}
    print(f"dist/index.html: (areas with {last} values, comparable with {base}) by level {by}; "
          f"metros dropped by the 5% rule: {len(jump & set(ids))}; {len(html) / 1e6:.1f} MB")

if __name__ == "__main__":
    main()
