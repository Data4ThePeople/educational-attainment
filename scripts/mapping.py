"""Map B15003 and B15002 lines to the five attainment groups by label.

Line numbers move between years (2025 B15003 drops two lines), so every
year's lines are read from that year's variables_<table>.json and mapped by
their label text. Any label not listed here stops the build.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

GROUPS = ["lths", "hs", "somecol", "ba", "grad"]
GROUP_NAMES = {
    "lths": "Less than high school",
    "hs": "High school or equivalent",
    "somecol": "Some college or associate's",
    "ba": "Bachelor's",
    "grad": "Graduate or professional",
}

# label -> (group, detail flag). Detail flags mark the lines that make up
# the comparable "less than grade 1" (B15003) and "less than 5th grade"
# (B15002) series.
B15003_MAP = {
    "no schooling completed": ("lths", "lt1"),
    "nursery school": ("lths", "lt1"),
    "kindergarten": ("lths", "lt1"),
    "less than grade 1": ("lths", "lt1"),
    **{f"{g} grade": ("lths", None) for g in
       ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th", "11th"]},
    "12th grade, no diploma": ("lths", None),
    "regular high school diploma": ("hs", None),
    "ged or alternative credential": ("hs", None),
    "some college, less than 1 year": ("somecol", None),
    "some college, 1 or more years, no degree": ("somecol", None),
    "associate's degree": ("somecol", None),
    "bachelor's degree": ("ba", None),
    "master's degree": ("grad", None),
    "professional school degree": ("grad", None),
    "doctorate degree": ("grad", None),
}

B15002_MAP = {
    "no schooling completed": ("lths", "lt5"),
    "nursery to 4th grade": ("lths", "lt5"),
    "less than grade 1": ("lths", "lt5"),
    "1st to 4th grade": ("lths", "lt5"),
    "5th and 6th grade": ("lths", None),
    "7th and 8th grade": ("lths", None),
    "9th grade": ("lths", None),
    "10th grade": ("lths", None),
    "11th grade": ("lths", None),
    "12th grade, no diploma": ("lths", None),
    "high school graduate (includes equivalency)": ("hs", None),
    "high school graduate, ged, or alternative": ("hs", None),
    "some college, less than 1 year": ("somecol", None),
    "some college, 1 or more years, no degree": ("somecol", None),
    "associate's degree": ("somecol", None),
    "bachelor's degree": ("ba", None),
    "master's degree": ("grad", None),
    "professional school degree": ("grad", None),
    "doctorate degree": ("grad", None),
}


def parts(label):
    """'Estimate!!Total:!!Male:!!9th grade' -> ['total', 'male', '9th grade']"""
    out = [re.sub(r":$", "", p.strip()).lower() for p in label.split("!!")]
    return [p for p in out if p != "estimate"]


def table_map(year, table):
    """Return {line_id: (group or 'total', detail, label)} for one year."""
    js = json.loads((RAW / str(year) / f"variables_{table}.json").read_text())
    lines = {}
    for var, meta in js["variables"].items():
        if not (var.startswith(table + "_") and var.endswith("E")):
            continue
        line = var[:-1]
        if line in lines:
            raise ValueError(f"duplicate line {line} in {year}")
        p = parts(meta["label"])
        if p == ["total"]:
            lines[line] = ("total", None, meta["label"])
            continue
        if table == "B15002":
            if len(p) == 2 and p[1] in ("male", "female"):
                continue  # sex subtotals, not needed
            key = p[2]
            m = B15002_MAP
        else:
            key = p[1]
            m = B15003_MAP
        if key not in m:
            raise ValueError(f"{table} {year} {line}: unmapped label {meta['label']!r}")
        g, d = m[key]
        lines[line] = (g, d, meta["label"])
    if sum(1 for v in lines.values() if v[0] == "total") != 1:
        raise ValueError(f"{table} {year}: expected one Total line")
    return dict(sorted(lines.items()))


def mapping_table(years, table="B15003"):
    """Rows of (label, group, detail, {year: line}) for DATASETS.md."""
    rows = {}
    for y in years:
        for line, (g, d, label) in table_map(y, table).items():
            key = parts(label)[-1]
            rows.setdefault(key, {"group": g, "detail": d, "years": {}})["years"][y] = line.split("_")[1]
    return rows


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from fetch import YEARS
    for t in ("B15003", "B15002"):
        for y in YEARS:
            m = table_map(y, t)
            print(t, y, len(m), "lines mapped")
