"""Write the two pages, each with the panel's published counts and MOEs
embedded. The pages compute every share, MOE and test themselves.

  dist/index.html  viz/map_template.html: 2025 map by state, county or metro
                   and micro area, with 2008 values and the change in the
                   tooltip. Shapes from data/clean/geo_paths.json (build_geo.py).
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


def build_map(lines_areas, area_info, big):
    """The map uses the same areas and the same comparability rule as the
    ranked view: a change since the first year is shown only for areas
    published in every year whose boundaries did not move their adult
    population by 5% or more in one year."""
    geo = json.loads((CLEAN / "geo_paths.json").read_text())
    years = sorted({y for a in lines_areas for y in a["y"]})
    first, last = years[0], years[-1]
    on_map = {f["id"] for lvl in ("state", "county", "cbsa") for f in geo[lvl]}
    areas = []
    for a in lines_areas:
        if a["id"] not in on_map or last not in a["y"]:
            continue
        rec = {"id": a["id"], "n": a["n"], "c": a["b"] and first in a["y"],
               "v": {y: a["y"][y] for y in (first, last) if y in a["y"]}}
        if not rec["c"]:
            if not area_info.loc[a["id"], "balanced"]:
                why = f"It was not published in every year from {first} to {last}, so no change since {first} is shown."
            else:
                why = (f"Boundary changes moved its adult population by 5% or more in one year, "
                       f"so no change since {first} is shown.")
            if a["id"].startswith("0500000US09"):
                why += " Connecticut replaced its counties with planning regions in 2022."
            rec["why"] = why
        areas.append(rec)
    us = next(a for a in lines_areas if a["id"] == "0100000US")
    data = {"groups": GROUPS, "first": first, "last": last, "us": us["y"], "areas": areas}
    html = (ROOT / "viz" / "map_template.html").read_text()
    for k, v in (("DATA", data), ("GEO", geo)):
        assert f"/*{k}*/null" in html
        html = html.replace(f"/*{k}*/null", json.dumps(v, separators=(",", ":")))
    (ROOT / "dist" / "index.html").write_text(html)
    by = {lvl: sum(f["id"] in {x["id"] for x in areas} for f in geo[lvl]) for lvl in ("state", "county", "cbsa")}
    print(f"dist/index.html: {len(areas)} areas with {last} values on the map {by}, {len(html) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
