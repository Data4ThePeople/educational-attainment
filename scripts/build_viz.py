"""Write dist/index.html: viz/template.html with the panel's published counts
and MOEs embedded. The page computes every share, MOE and test itself.
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
    (ROOT / "dist" / "index.html").write_text(html)
    print(f"dist/index.html: {len(out)} areas, {len(html) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
