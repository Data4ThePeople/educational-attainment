"""Build the clean panel from the raw API pulls.

Outputs in data/clean/:
  panel.csv            every area-year: five groups, total, and the less-than-
                       grade-1 detail line, as counts and shares with MOEs
  panel_b15002.csv     the same five groups from B15002 (sexes summed), a
                       cross-check only
  areas.csv            one row per GEOID: level, names seen, years present,
                       balanced-panel flag, break reasons
  change.csv           balanced panel: first year vs 2025 for each group,
                       with the z-test
  coverage.csv         B99151 allocation (imputation) rates
  mapping_B15003.csv   label -> group -> line number by year (for DATASETS.md)

MOE formulas: Census Bureau, "Understanding and Using American Community
Survey Data: What All Data Users Need to Know" (2020), chapter 8, formula (1)
for sums and formula (6) for proportions (formula (7), the ratio form, when
the value under the root is negative); chapter 7, formulas (1) and (3) for
standard errors and the significance test.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from mapping import GROUPS, RAW, ROOT, mapping_table, table_map  # noqa: E402

CLEAN = ROOT / "data" / "clean"
YEARS = [y for y in range(2008, 2026) if y != 2020]
LEVELS = ["us", "region", "division", "state", "county", "cbsa", "place"]
Z90 = 1.645
# Fill area-years where B15003 is withheld with the same five groups from
# B15002. Set False to use B15003 only.
FILL_FROM_B15002 = True

# Census annotation codes that can appear in place of an estimate or MOE.
MOE_CONTROLLED = -555555555   # estimate is controlled; MOE is not applicable (0)
BAD_CODES = {-999999999, -888888888, -666666666, -333333333, -222222222}


def load(year, table, level):
    path = RAW / str(year) / f"{table}_{level}.json"
    if not path.exists():
        return None
    js = json.loads(path.read_text())
    df = pd.DataFrame(js[1:], columns=js[0])
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def num(s):
    return pd.to_numeric(s, errors="coerce")


def build_table(table):
    rows = []
    for year in YEARS:
        lines = table_map(year, table)
        for level in LEVELS:
            df = load(year, table, level)
            if df is None:
                continue
            out = pd.DataFrame({"geoid": df["GEO_ID"], "geo_id_raw": df["GEO_ID"],
                                "name": df["NAME"], "level": level, "year": year})
            if level == "cbsa":
                # Census GEO_IDs for metro areas embed the OMB delineation
                # vintage (310M100US..., 310M700US...), so the same CBSA code
                # gets a new GEO_ID with every delineation update. Track by the
                # CBSA code; keep the raw GEO_ID and its vintage component.
                out["geoid"] = "310XX00US" + df["GEO_ID"].str[-5:]
                out["vintage"] = df["GEO_ID"].str[3:7]
            if level == "state":
                out.loc[out.geoid.str.endswith("US72"), "level"] = "pr"
            bad = pd.Series(False, index=df.index)
            parts = {}
            for line, (g, d, _) in lines.items():
                e = num(df[line + "E"])
                m = num(df[line + "M"])
                bad |= e.isna() | e.isin(BAD_CODES) | m.isna() | m.isin(BAD_CODES)
                m = m.where(m != MOE_CONTROLLED, 0)
                for key in {g, d} - {None}:
                    pe, pm2 = parts.get(key, (0, 0))
                    parts[key] = (pe + e, pm2 + m ** 2)
            for key, (e, m2) in parts.items():
                out[f"{key}_est"] = e
                out[f"{key}_moe"] = np.sqrt(m2)
            out["bad_values"] = bad
            rows.append(out)
    df = pd.concat(rows, ignore_index=True)
    dup = df.duplicated(["geoid", "year"])
    if dup.any():
        raise ValueError(f"duplicate geoid-year rows:\n{df[dup].head()}")
    # The detail lines must add up to the published total.
    s = df[[f"{g}_est" for g in GROUPS]].sum(axis=1)
    off = (s - df.total_est).abs() > 0
    if off.any():
        raise ValueError(f"{table}: {off.sum()} rows where groups do not sum to total")
    return df


def add_shares(df, keys):
    y, my = df.total_est, df.total_moe
    for k in keys:
        x, mx = df[f"{k}_est"], df[f"{k}_moe"]
        p = x / y
        rad = mx ** 2 - p ** 2 * my ** 2
        rad = rad.where(rad >= 0, mx ** 2 + p ** 2 * my ** 2)
        df[f"{k}_share"] = 100 * p
        df[f"{k}_share_moe"] = 100 * np.sqrt(rad) / y
    return df


def areas_table(df):
    full = set(YEARS)
    recs = []
    for gid, g in df.groupby("geoid"):
        yrs = sorted(g.year)
        g = g.sort_values("year")
        names = g["name"].unique().tolist()
        latest = g["name"].iloc[-1]   # the name in the latest published year
        reasons = []
        if yrs[0] > YEARS[0]:
            reasons.append(f"first published {yrs[0]}")
        if yrs[-1] < YEARS[-1]:
            reasons.append(f"last published {yrs[-1]}")
        gaps = sorted(full - set(yrs) - set(range(0, yrs[0])) - set(range(yrs[-1] + 1, 3000)))
        if gaps:
            reasons.append("missing " + ", ".join(map(str, gaps)))
        if len(names) > 1:
            reasons.append("name changed: " + " -> ".join(names))
        recs.append({
            "geoid": gid, "level": g.level.iloc[-1], "name": latest,
            "n_years": len(yrs), "first": yrs[0], "last": yrs[-1],
            "balanced": set(yrs) == full,
            "bad_values": bool(g.bad_values.any()),
            "reasons": "; ".join(reasons),
        })
    return pd.DataFrame(recs)


def change_table(df, balanced):
    a = df[df.geoid.isin(balanced) & df.year.isin([YEARS[0], YEARS[-1]])]
    first = a[a.year == YEARS[0]].set_index("geoid")
    last = a[a.year == YEARS[-1]].set_index("geoid")
    recs = []
    for g in GROUPS:
        p1, m1 = first[f"{g}_share"], first[f"{g}_share_moe"]
        p2, m2 = last[f"{g}_share"], last[f"{g}_share_moe"]
        se = np.sqrt((m1 / Z90) ** 2 + (m2 / Z90) ** 2)
        z = (p2 - p1) / se
        recs.append(pd.DataFrame({
            "geoid": last.index, "level": last.level, "name": last.name, "group": g,
            "share_first": p1.reindex(last.index), "moe_first": m1.reindex(last.index),
            "share_last": p2, "moe_last": m2,
            "change_pts": (p2 - p1.reindex(last.index)), "z": z.reindex(last.index),
        }))
    out = pd.concat(recs, ignore_index=True)
    out["significant"] = out.z.abs() > Z90
    return out


def coverage():
    rows = []
    for year in YEARS:
        for level in LEVELS:
            df = load(year, "B99151", level)
            if df is None:
                continue
            tot, alloc = num(df["B99151_001E"]), num(df["B99151_002E"])
            for gid, name, t, a in zip(df.GEO_ID, df.NAME, tot, alloc):
                rows.append({"geoid": gid, "name": name, "level": level, "year": year,
                             "total": t, "allocated": a,
                             "alloc_pct": 100 * a / t if t else np.nan})
    return pd.DataFrame(rows)


def fill_withheld(df, b2):
    """B15003 is withheld (all nulls) for some area-years over 65,000 under the
    Census Bureau's data-quality filtering of 1-year detailed tables. Where
    B15002 is published for the same area-year, take the five groups and the
    total from it: where both tables exist, their five-group counts match
    exactly (checked in findings.py). The less-than-grade-1 detail stays empty.
    Area-years with neither table are dropped and listed as withheld.
    """
    df["source"] = np.where(df.total_est.isna(), "withheld", "B15003")
    if FILL_FROM_B15002:
        cols = ["total_est", "total_moe"] + [f"{g}_{k}" for g in GROUPS for k in ("est", "moe")]
        key = ["geoid", "year"]
        donor = b2.set_index(key)[cols]
        idx = df.set_index(key).index
        need = (df.source == "withheld").values & idx.isin(donor.index[donor.total_est.notna()])
        df.loc[need, cols] = donor.loc[idx[need], cols].values
        df.loc[need, "source"] = "B15002"
    withheld = df[df.source == "withheld"][["geoid", "name", "level", "year"]]
    return df[df.source != "withheld"].reset_index(drop=True), withheld


def main():
    CLEAN.mkdir(parents=True, exist_ok=True)
    keys = GROUPS + ["lt1"]
    b2 = add_shares(build_table("B15002"), GROUPS + ["lt5"])
    b2.to_csv(CLEAN / "panel_b15002.csv", index=False, float_format="%.4f")

    df, withheld = fill_withheld(build_table("B15003"), b2)
    df = add_shares(df, keys)
    df.to_csv(CLEAN / "panel.csv", index=False, float_format="%.4f")
    withheld.to_csv(CLEAN / "withheld.csv", index=False)
    print("panel:", len(df), "rows;", df.source.value_counts().to_dict(), "; withheld:", len(withheld))

    areas = areas_table(df)
    wh = withheld.groupby("geoid").year.apply(lambda s: ", ".join(map(str, sorted(s))))
    fill = df[df.source == "B15002"].groupby("geoid").year.apply(lambda s: ", ".join(map(str, sorted(s))))
    areas["withheld_years"] = areas.geoid.map(wh).fillna("")
    areas["b15002_years"] = areas.geoid.map(fill).fillna("")
    # A missing year is either below the 65,000 threshold (no row at all) or
    # published but withheld; say which.
    has_wh = areas.withheld_years != ""
    areas.loc[has_wh, "reasons"] = (areas.loc[has_wh, "reasons"].fillna("") +
                                    "; table published with no values in " + areas.loc[has_wh, "withheld_years"]).str.lstrip("; ")
    areas.to_csv(CLEAN / "areas.csv", index=False)
    balanced = set(areas.loc[areas.balanced, "geoid"])
    print(areas.groupby("level").balanced.agg(["sum", "count"]))

    ch = change_table(df, balanced)
    ch.to_csv(CLEAN / "change.csv", index=False, float_format="%.4f")

    coverage().to_csv(CLEAN / "coverage.csv", index=False, float_format="%.3f")

    mt = mapping_table(YEARS)
    pd.DataFrame([{"label": k, "group": v["group"], "lt1": v["detail"] == "lt1",
                   **{str(y): v["years"].get(y, "") for y in YEARS}}
                  for k, v in mt.items()]).to_csv(CLEAN / "mapping_B15003.csv", index=False)


if __name__ == "__main__":
    main()
