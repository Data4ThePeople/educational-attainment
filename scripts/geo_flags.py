"""Flag boundary changes that a stable GEOID hides.

Metro and micro areas: compare each CBSA's list of counties across the OMB
delineation files that each ACS year used (data/raw/delineations/, saved as
downloaded from www2.census.gov/programs-surveys/metro-micro/geographies/
reference-files/). Counties: known code and boundary changes from the Census
Bureau's "Substantial Changes to Counties" pages.

Writes data/clean/geo_flags.csv (geoid, note) and data/clean/cbsa_changes.csv.
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from mapping import ROOT  # noqa: E402

DELIN = ROOT / "data" / "raw" / "delineations"
CLEAN = ROOT / "data" / "clean"

# Delineation used by each ACS 1-year year, from the ACS "Geography
# Boundaries by Year" pages. 2008 is not stated by the Census Bureau; we
# assume the November 2007 file (the latest at the time) and say so.
VINTAGE_FILE = {
    "2007-11": "2007_historical-delineation-files_list1.txt",
    "2008-11": "2008_historical-delineation-files_list1.txt",
    "2009-12": "2009_historical-delineation-files_list1.txt",
    "2013-02": "2013_delineation-files_list1.xls",
    "2015-07": "2015_delineation-files_list1.xls",
    "2017-08": "2017_delineation-files_list1.xls",
    "2018-09": "2018_delineation-files_list1_Sep_2018.xls",
    "2020-03": "2020_delineation-files_list1_2020.xls",
    "2023-07": "2023_delineation-files_list1_2023.xlsx",
}
YEAR_VINTAGE = {2008: "2007-11", 2009: "2008-11", 2010: "2009-12", 2011: "2009-12", 2012: "2009-12",
                2013: "2013-02", 2014: "2013-02", 2015: "2013-02", 2016: "2015-07", 2017: "2015-07",
                2018: "2017-08", 2019: "2018-09", 2021: "2020-03", 2022: "2020-03",
                2023: "2023-07", 2024: "2023-07", 2025: "2023-07"}

COUNTY_NOTES = {
    "0500000US51019": "Bedford city, Virginia, became part of Bedford County in 2013; the county's boundary is larger from 2014 on.",
}
CT_NOTE = ("Connecticut replaced its eight counties with nine planning regions in the 2022 ACS, "
           "so county series in Connecticut end in 2021 or start in 2022.")


def read_txt(path):
    out = {}
    for line in path.read_text(errors="replace").splitlines():
        cbsa, fips = line[0:5], line[16:21]
        if re.fullmatch(r"\d{5}", cbsa) and re.fullmatch(r"\d{5}", fips):
            out.setdefault(cbsa, set()).add(fips)
    return out


def read_xls(path):
    raw = pd.read_excel(path, header=None, dtype=str)
    hdr = raw.index[raw.apply(lambda r: r.astype(str).str.strip().eq("CBSA Code").any(), axis=1)][0]
    df = raw.iloc[hdr + 1:].copy()
    df.columns = [str(c).strip() for c in raw.iloc[hdr]]
    df = df[df["CBSA Code"].astype(str).str.fullmatch(r"\d{5}")]
    fips = df["FIPS State Code"].str.zfill(2) + df["FIPS County Code"].str.zfill(3)
    out = {}
    for c, f in zip(df["CBSA Code"], fips):
        out.setdefault(c, set()).add(f)
    return out


def main():
    comp = {v: (read_txt if f.endswith(".txt") else read_xls)(DELIN / f) for v, f in VINTAGE_FILE.items()}
    for v, d in comp.items():
        assert len(d) > 900, f"{v}: only {len(d)} CBSAs parsed"
    areas = pd.read_csv(CLEAN / "areas.csv")
    p = pd.read_csv(CLEAN / "panel.csv", usecols=["geoid", "year"])
    rows, notes = [], {}
    for gid in areas.loc[areas.level == "cbsa", "geoid"]:
        code = gid[-5:]
        yrs = sorted(p.loc[p.geoid == gid, "year"])
        vints = sorted({YEAR_VINTAGE[y] for y in yrs})
        changes = []
        for a, b in zip(vints, vints[1:]):
            sa, sb = comp[a].get(code, set()), comp[b].get(code, set())
            if sa != sb:
                first = min(y for y in yrs if YEAR_VINTAGE[y] == b)
                ct = any(f.startswith("09") for f in sa | sb) and b == "2023-07"
                added, removed = sorted(sb - sa), sorted(sa - sb)
                rows.append({"geoid": gid, "first_year_new": first, "from": a, "to": b,
                             "added": " ".join(added), "removed": " ".join(removed), "connecticut": ct})
                if ct:
                    changes.append(f"{first} (Connecticut planning regions replaced its counties)")
                else:
                    cnt = lambda n, w: f"{n} {'county' if n == 1 else 'counties'} {w}"
                    changes.append(f"{first} ({cnt(len(added), 'added')}, {cnt(len(removed), 'removed')})")
        if changes:
            notes[gid] = ("Its county makeup changed with new OMB delineations, first used in "
                          + "; ".join(changes) + ".")
        if 2008 in yrs:
            notes[gid] = (notes.get(gid, "") + " The Census Bureau does not state which delineation "
                          "its 2008 metro data used; we assume November 2007.").strip()
    for gid, n in COUNTY_NOTES.items():
        notes[gid] = n
    for gid in areas.loc[(areas.level == "county") & areas.geoid.str.startswith("0500000US09"), "geoid"]:
        notes[gid] = CT_NOTE
    pd.DataFrame(rows).to_csv(CLEAN / "cbsa_changes.csv", index=False)
    pd.DataFrame([{"geoid": k, "note": v} for k, v in notes.items()]).to_csv(CLEAN / "geo_flags.csv", index=False)
    ch = pd.DataFrame(rows)
    bal = set(areas.loc[areas.balanced, "geoid"])
    print(f"CBSAs with a composition change: {ch.geoid.nunique()} "
          f"(balanced: {ch[ch.geoid.isin(bal)].geoid.nunique()} of {len(bal & set(areas.loc[areas.level == 'cbsa', 'geoid']))}); "
          f"by first year: {ch[ch.geoid.isin(bal)].groupby('first_year_new').geoid.nunique().to_dict()}")


if __name__ == "__main__":
    main()
