"""Checks and summary tables behind FINDINGS.md.

Writes data/clean/findings_tables.md. Every number in FINDINGS.md comes from
this file.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from mapping import GROUPS, GROUP_NAMES, ROOT  # noqa: E402

CLEAN = ROOT / "data" / "clean"
Z90 = 1.645
OUT = []


def h(t):
    OUT.extend(["", f"## {t}", ""])


def table(df, floatfmt="{:.2f}"):
    df = df.copy()
    cols = list(df.columns)
    OUT.append("| " + " | ".join(map(str, cols)) + " |")
    OUT.append("|" + "---|" * len(cols))
    for _, r in df.iterrows():
        OUT.append("| " + " | ".join(floatfmt.format(v) if isinstance(v, (float, np.floating)) else str(v)
                                     for v in r) + " |")


def z(p1, m1, p2, m2):
    return (p2 - p1) / np.sqrt((m1 / Z90) ** 2 + (m2 / Z90) ** 2)


def main():
    p = pd.read_csv(CLEAN / "panel.csv")
    areas = pd.read_csv(CLEAN / "areas.csv")
    ch = pd.read_csv(CLEAN / "change.csv")
    years = sorted(p.year.unique())

    h("Areas published per level per year")
    t = p.groupby(["level", "year"]).size().unstack(fill_value=0)
    t.columns = [str(c) for c in t.columns]
    table(t.reset_index())
    bal = areas.groupby("level").agg(areas=("geoid", "size"), balanced=("balanced", "sum")).reset_index()
    OUT.append("")
    table(bal)

    h("Check: do the five groups move unusually from 2024 to 2025? (nation)")
    us = p[p.level == "us"].set_index("year")
    rows = []
    for g in GROUPS:
        r = {"group": GROUP_NAMES[g]}
        for a, b in [(2021, 2022), (2022, 2023), (2023, 2024), (2024, 2025)]:
            d = us.at[b, f"{g}_share"] - us.at[a, f"{g}_share"]
            zz = z(us.at[a, f"{g}_share"], us.at[a, f"{g}_share_moe"], us.at[b, f"{g}_share"], us.at[b, f"{g}_share_moe"])
            r[f"{a}-{b}"] = f"{d:+.2f} (z {zz:+.1f})"
        diffs = [us.at[b, f"{g}_share"] - us.at[b - 1, f"{g}_share"] for b in years if b - 1 in us.index and b > 2008]
        r["typical yearly change, 2009-2024 (median abs)"] = f"{np.median(np.abs(diffs[:-1])):.2f}"
        rows.append(r)
    table(pd.DataFrame(rows))

    h("Check: share of states (with DC) with a significant one-year change, by group")
    st = p[p.level == "state"]
    rows = []
    for g in GROUPS:
        r = {"group": GROUP_NAMES[g]}
        for a, b in [(2017, 2018), (2018, 2019), (2021, 2022), (2022, 2023), (2023, 2024), (2024, 2025)]:
            A = st[st.year == a].set_index("geoid")
            B = st[st.year == b].set_index("geoid")
            zz = z(A[f"{g}_share"], A[f"{g}_share_moe"], B[f"{g}_share"], B[f"{g}_share_moe"])
            r[f"{a}-{b}"] = f"{(zz.abs() > Z90).mean() * 100:.0f}%"
        rows.append(r)
    table(pd.DataFrame(rows))

    h("Check: the less-than-grade-1 detail line (nation)")
    lt = us[["lt1_share", "lt1_share_moe", "lths_share"]].reset_index()
    table(lt, "{:.3f}")
    s24 = st[st.year == 2024].set_index("geoid")
    s25 = st[st.year == 2025].set_index("geoid")
    fell = (s25.lt1_share < s24.lt1_share).sum()
    zz = z(s24.lt1_share, s24.lt1_share_moe, s25.lt1_share, s25.lt1_share_moe)
    OUT.append("")
    OUT.append(f"States with a lower less-than-grade-1 share in 2025 than 2024: {fell} of {len(s25)}; "
               f"significant falls: {((zz < -Z90)).sum()}; significant rises: {(zz > Z90).sum()}.")

    h("Check: where did the 2025 drop in less-than-grade-1 go? (nation, detail lines)")
    import json
    from mapping import RAW, table_map
    det = {}
    for y in [2021, 2024, 2025]:
        js = json.loads((RAW / str(y) / "B15003_us.json").read_text())
        d = dict(zip(js[0], js[1]))
        tot = float(d["B15003_001E"])
        for line, (g, dd, lab) in table_map(y, "B15003").items():
            if g == "total":
                continue
            k = "Less than grade 1 (old three lines summed)" if dd == "lt1" else lab.split("!!")[-1]
            det.setdefault(k, {"group": GROUP_NAMES[g]})
            det[k][y] = det[k].get(y, 0) + 100 * float(d[line + "E"]) / tot
    dt = pd.DataFrame(det).T
    dt["2024-2025 change"] = dt[2025] - dt[2024]
    dt["avg yearly change 2021-2024"] = (dt[2024] - dt[2021]) / 3
    dt["beyond trend"] = dt["2024-2025 change"] - dt["avg yearly change 2021-2024"]
    table(dt.reset_index().rename(columns={"index": "line"})[["line", "group", 2024, 2025, "2024-2025 change",
                                                             "avg yearly change 2021-2024", "beyond trend"]].astype({2024: float, 2025: float, "2024-2025 change": float, "avg yearly change 2021-2024": float, "beyond trend": float}), "{:.3f}")
    bt = dt.groupby("group")["beyond trend"].sum()
    OUT.append("")
    OUT.append("Beyond-trend change by group: " + ", ".join(f"{k}: {v:+.2f}" for k, v in bt.items()))

    h("Check: do areas with a bigger 2025 drop in less-than-grade-1 show a bigger unusual change in the five groups?")
    OUT.append("Unusual change = 2024-2025 change minus the 2021-2024 average yearly change. "
               "Slope and correlation are across areas, against the 2024-2025 change in the less-than-grade-1 share.")
    OUT.append("")
    rows = []
    src = p[p.source == "B15003"]
    for lv in ["state", "county", "cbsa", "place"]:
        a = src[src.level == lv].pivot_table(index="geoid", columns="year",
                                             values=[f"{g}_share" for g in GROUPS] + ["lt1_share"])
        a = a.dropna(subset=[(f"{g}_share", y) for g in GROUPS for y in (2021, 2024, 2025)] +
                     [("lt1_share", 2024), ("lt1_share", 2025)])
        dl = a["lt1_share"][2025] - a["lt1_share"][2024]
        r = {"level": lv, "areas": len(a), "mean lt1 change": dl.mean()}
        for g in GROUPS:
            s = a[f"{g}_share"]
            exc = (s[2025] - s[2024]) - (s[2024] - s[2021]) / 3
            r[f"{GROUP_NAMES[g]}: slope / r / mean"] = (f"{np.polyfit(dl, exc, 1)[0]:+.2f} / "
                                                       f"{np.corrcoef(dl, exc)[0, 1]:+.2f} / {exc.mean():+.2f}")
        rows.append(r)
    table(pd.DataFrame(rows))

    h("Withheld tables and the B15002 fill")
    wh = pd.read_csv(CLEAN / "withheld.csv")
    OUT.append(f"Area-years where B15003 is withheld (published with no values): {(p.source == 'B15002').sum() + len(wh)}. "
               f"Filled from B15002: {(p.source == 'B15002').sum()}. Withheld in both, dropped: {len(wh)}.")
    OUT.append("")
    t = p[p.source == "B15002"].groupby(["year", "level"]).size().unstack(fill_value=0)
    table(t.reset_index())
    bal_ids = set(areas.loc[areas.balanced, "geoid"])
    uses = p[p.geoid.isin(bal_ids) & (p.source == "B15002")].groupby("level").geoid.nunique()
    OUT.append("")
    OUT.append("Balanced-panel areas that need at least one B15002 year: " +
               ", ".join(f"{k}: {v}" for k, v in uses.items()))

    h("Check: B15002 (sexes summed) vs B15003 five-group shares")
    b2 = pd.read_csv(CLEAN / "panel_b15002.csv")
    m = p[p.source == "B15003"].merge(b2, on=["geoid", "year"], suffixes=("", "_b2"))
    m = m[m.total_est_b2.notna()]
    worst = max((m[f"{g}_share"] - m[f"{g}_share_b2"]).abs().max() for g in GROUPS)
    tot = (m.total_est - m.total_est_b2).abs().max()
    OUT.append(f"{len(m)} area-years matched. Largest share difference: {worst:.4f} points. "
               f"Largest total difference: {tot:.0f} people. Rows in B15003 only: {len(p) - len(m)}.")
    lt5 = b2[b2.level == "us"][["year", "lt5_share"]]
    OUT.append("")
    OUT.append("B15002 less-than-5th-grade share, nation (comparable across 2025):")
    OUT.append("")
    table(lt5, "{:.3f}")

    h("Coverage check: share of attainment answers filled in by the Census Bureau (B99151)")
    cov = pd.read_csv(CLEAN / "coverage.csv")
    t = cov[cov.level.isin(["us"])].pivot_table(index="year", values="alloc_pct").rename(columns={"alloc_pct": "nation"})
    for lv in ["state", "county", "cbsa", "place"]:
        t[f"{lv} median"] = cov[cov.level == lv].groupby("year").alloc_pct.median()
        t[f"{lv} max"] = cov[cov.level == lv].groupby("year").alloc_pct.max()
    table(t.reset_index(), "{:.1f}")

    h("MOE widening: median share MOE (points) by level and year")
    rows = []
    for lv in ["state", "county", "cbsa", "place"]:
        for g in ["lths", "ba"]:
            r = {"level": lv, "group": GROUP_NAMES[g]}
            for y in [2019, 2022, 2023, 2024, 2025]:
                r[str(y)] = p[(p.level == lv) & (p.year == y)][f"{g}_share_moe"].median()
            r["2025 vs 2024"] = f"{(r['2025'] / r['2024'] - 1) * 100:+.0f}%"
            rows.append(r)
    table(pd.DataFrame(rows))

    h("Population 25+ (count): change 2024 to 2025 vs earlier years, nation")
    tot = us.total_est
    OUT.append(" | ".join(f"{y}: {tot[y]:,.0f}" for y in years))
    yo = [(y, (tot[y] / tot[y - 1] - 1) * 100) for y in years if y - 1 in tot.index]
    OUT.append("")
    OUT.append("Yearly growth: " + ", ".join(f"{y}: {g:+.2f}%" for y, g in yo))

    h(f"Significant changes, {years[0]} to {years[-1]}, balanced panel")
    rows = []
    for (lv, g), d in ch.groupby(["level", "group"]):
        rows.append({"level": lv, "group": GROUP_NAMES[g], "areas": len(d),
                     "significant": int(d.significant.sum()),
                     "up": int((d.significant & (d.change_pts > 0)).sum()),
                     "down": int((d.significant & (d.change_pts < 0)).sum()),
                     "median change": d.change_pts.median()})
    table(pd.DataFrame(rows))
    n = len(ch[ch.level.isin(["state", "county", "cbsa", "place"])])
    OUT.append("")
    OUT.append(f"Tests across states, counties, metro areas and places: {n}. If nothing had changed anywhere, "
               f"about 10% ({n * 0.10:.0f}) would pass at 90% confidence by chance.")

    h("Nation and regions, first year vs 2025")
    t = ch[ch.level.isin(["us", "region", "division"])][["name", "group", "share_first", "share_last", "change_pts", "z", "significant"]]
    t["group"] = t.group.map(GROUP_NAMES)
    table(t)

    h("Largest significant changes by level (top 5 up, top 5 down)")
    for lv in ["state", "county", "cbsa", "place"]:
        for g in GROUPS:
            d = ch[(ch.level == lv) & (ch.group == g) & ch.significant].sort_values("change_pts")
            if d.empty:
                continue
            OUT.append(f"**{lv}, {GROUP_NAMES[g]}**")
            OUT.append("")
            show = pd.concat([d.tail(5).iloc[::-1], d.head(5)]).drop_duplicates("geoid")
            table(show[["name", "share_first", "share_last", "change_pts", "z"]])
            OUT.append("")

    h("Graduate + bachelor's combined, states: first year vs 2025 (for context only)")
    a = p[(p.level == "state") & p.year.isin([years[0], years[-1]])].copy()
    a["ba_plus"] = a.ba_share + a.grad_share
    t = a.pivot_table(index="name", columns="year", values="ba_plus")
    t["change"] = t[years[-1]] - t[years[0]]
    t = t.sort_values("change", ascending=False)
    OUT.append(f"Largest: {t.index[0]} {t.change.iloc[0]:+.1f}; smallest: {t.index[-1]} {t.change.iloc[-1]:+.1f} points.")

    h("Spot checks: areas with the largest less-than-high-school falls")
    for name in ["McKinley County, New Mexico", "Gallup, NM Micro Area", "Apache County, Arizona",
                 "Arecibo Municipio, Puerto Rico", "Rockland County, New York", "Sumter County, Florida"]:
        a = p[p.name == name].set_index("year")
        if a.empty:
            continue
        OUT.append(f"- {name}: less than HS " + ", ".join(f"{y}: {a.at[y, 'lths_share']:.1f}" for y in a.index if y in (2008, 2019, 2021, 2023, 2024, 2025)) +
                   "; less than grade 1 " + ", ".join(f"{y}: {a.at[y, 'lt1_share']:.1f}" for y in a.index if y in (2008, 2019, 2024, 2025) and pd.notna(a.at[y, 'lt1_share'])) +
                   f"; source years from B15002: {', '.join(str(y) for y in a.index[a.source == 'B15002']) or 'none'}")

    h("Areas where the less-than-grade-1 line makes up most of the less-than-high-school fall, 2008 to 2024")
    OUT.append("2024 is used as the end year so the 2025 question change is not part of it. Balanced panel, "
               "B15003 years only, falls of 2 points or more in less than high school.")
    OUT.append("")
    a = p[p.geoid.isin(areas.loc[areas.balanced, "geoid"]) & p.year.isin([2008, 2024]) & (p.source == "B15003")]
    a = a.pivot_table(index=["geoid", "name", "level"], columns="year", values=["lths_share", "lt1_share"]).dropna()
    d_l = a["lths_share"][2024] - a["lths_share"][2008]
    d_1 = a["lt1_share"][2024] - a["lt1_share"][2008]
    frac = d_1 / d_l
    sel = (d_l <= -2) & (frac >= 0.5)
    t = pd.DataFrame({"lths 2008": a["lths_share"][2008], "lths 2024": a["lths_share"][2024],
                      "lths change": d_l, "lt1 change": d_1, "lt1 part of fall": frac})[sel]
    t = t.sort_values("lt1 part of fall", ascending=False).reset_index()
    table(t)
    OUT.append("")
    OUT.append(f"Areas listed: {len(t)} of {(d_l <= -2).sum()} with a fall of 2 points or more.")

    h("Metro areas whose county makeup changed: size of the change")
    cc = pd.read_csv(CLEAN / "cbsa_changes.csv", dtype={"first_year_new": int})
    bal_c = cc[cc.geoid.isin(areas.loc[areas.balanced, "geoid"])]
    tot = p[p.level == "cbsa"].pivot_table(index="geoid", columns="year", values="total_est")
    recs = []
    for _, r in bal_c.iterrows():
        y = r.first_year_new
        prev = max(v for v in tot.columns if v < y)
        jump = (tot.at[r.geoid, y] / tot.at[r.geoid, prev] - 1) * 100
        recs.append({"geoid": r.geoid, "name": areas.set_index("geoid").at[r.geoid, "name"], "year": y,
                     "pop 25+ change from prior year (%)": jump})
    j = pd.DataFrame(recs)
    big = j[j["pop 25+ change from prior year (%)"].abs() >= 5].sort_values("pop 25+ change from prior year (%)")
    OUT.append(f"Balanced metro areas with a change: {bal_c.geoid.nunique()} of "
               f"{int(((areas.level == 'cbsa') & areas.balanced).sum())}. Changes where the population 25 and over "
               f"jumped 5% or more in the switch year: {len(big)}.")
    OUT.append("")
    table(big)
    big[["geoid"]].drop_duplicates().to_csv(CLEAN / "cbsa_big_changes.csv", index=False)
    ranked = (ch.level == "cbsa") & ~ch.geoid.isin(big.geoid)
    OUT.append("")
    OUT.append(f"Metro areas left in the ranked view: {ch[ranked].geoid.nunique()}.")
    rows = []
    for g, d in ch[ranked].groupby("group"):
        rows.append({"group": GROUP_NAMES[g], "areas": len(d), "significant": int(d.significant.sum()),
                     "up": int((d.significant & (d.change_pts > 0)).sum()),
                     "down": int((d.significant & (d.change_pts < 0)).sum()), "median change": d.change_pts.median()})
    table(pd.DataFrame(rows))

    h("Broken series by level and reason")
    br = areas[~areas.balanced].copy()
    for lv, d in br.groupby("level"):
        starts = d.reasons.str.contains("first published").sum()
        ends = d.reasons.str.contains("last published").sum()
        gaps = d.reasons.str.contains("missing").sum()
        names = d.reasons.str.contains("name changed").sum()
        OUT.append(f"- {lv}: {len(d)} areas; start after {years[0]}: {starts}; end before {years[-1]}: {ends}; "
                   f"gaps: {gaps}; name changed: {names}")
    nm = areas[areas.balanced & areas.reasons.fillna("").str.contains("name changed")]
    OUT.append("")
    OUT.append(f"Balanced-panel areas whose published name changed: {len(nm)}")

    (CLEAN / "findings_tables.md").write_text("# Findings tables (generated by scripts/findings.py)\n" + "\n".join(OUT) + "\n")
    print("\n".join(OUT))


if __name__ == "__main__":
    main()
