"""Student loan debt by education, adults 25 and over, 2016 and 2025, from
the Survey of Consumer Finances (SCF) full public data. Run fetch_scf.py
first.

The SCF asks for each of up to six student loans how much is still owed and
whose education it paid for. A person's own student debt is the sum of the
loans for their own education. Each family's reference person and, where
present, spouse or partner is a person here, with their own age and highest
degree. Loans for a child or other relative, loans coded "multiple people"
(a code first offered in 2025), and the combined balance of a family's
seventh and later loans (whose education they paid for was not asked in
2016) are not assigned to anyone; their share of all balances is reported.

Estimates average the five implicates. Standard errors follow the SCF
codebook's MEANIT macro: sqrt(6/5 * imputation variance + replicate
variance), with the replicate variance from the 999 replicate weights
(times the multiplicity factors) on the first implicate.

Dollars are moved to 2025 dollars with the R-CPI-U-RS annual averages used
for pay (build_viz.cpi_annual).

Writes data/clean/scf_debt.csv and data/clean/scf_debt_tables.md.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from mapping import RAW, ROOT  # noqa: E402
from build_viz import cpi_annual  # noqa: E402

CLEAN = ROOT / "data" / "clean"
X = RAW / "scf" / "x"
YEARS = (2016, 2025)
Z90 = 1.645
WHOSE = ["x7978", "x7883", "x7888", "x7893", "x7898", "x7993"]
OWED = ["x7824", "x7847", "x7870", "x7924", "x7947", "x7970"]
COLS = ["y1", "yy1", "x42001", "x14", "x19", "x5931", "x6111", "x7801", "x7179"] + WHOSE + OWED
# Highest degree (X5931 reference person, X6111 spouse/partner); the public
# data combine doctorate (15) with professional (14).
DEGREE = {"lths": range(-1, 8), "hs": [8], "somecol": [9, 10, 11], "ba": [12], "ma": [13], "prof": [14]}
GROUPS = {"lths": ["lths"], "hs": ["hs"], "somecol": ["somecol"], "ba": ["ba"], "grad": ["ma", "prof"],
          "ma": ["ma"], "prof": ["prof"], "all": list(DEGREE)}
NAMES = {"lths": "Less than high school", "hs": "High school or equivalent",
         "somecol": "Some college or associate's", "ba": "Bachelor's", "grad": "Graduate or professional",
         "ma": "Master's", "prof": "Professional or doctorate", "all": "All adults 25 and over"}


def persons(year):
    d = pd.read_stata(X / f"scf{year}s" / f"p{str(year)[2:]}i6.dta", columns=COLS)
    d["imp"] = d.y1 % 10           # y1 = case id followed by the implicate digit
    assert set(d.imp) == {1, 2, 3, 4, 5}
    own = {1: 0.0, 2: 0.0}
    out = []
    owed = d[OWED].clip(lower=0).to_numpy()
    whose = d[WHOSE].to_numpy()
    rest_amt = d.x7179.clip(lower=0).to_numpy()
    total = owed.sum(axis=1) + rest_amt
    for p, age, deg in ((1, "x14", "x5931"), (2, "x19", "x6111")):
        mine = (owed * (whose == p)).sum(axis=1)
        own[p] = mine
        f = pd.DataFrame({"yy1": d.yy1, "imp": d.imp, "w": d.x42001, "age": d[age], "deg": d[deg], "debt": mine})
        if p == 2:
            f = f[d[deg] != 0]          # 0 = no spouse or partner in the family
        out.append(f)
    fam = pd.DataFrame({"imp": d.imp, "w": d.x42001, "total": total, "assigned": own[1] + own[2],
                        "child": (owed * (whose == 3)).sum(axis=1), "multiple": (owed * (whose == 6)).sum(axis=1),
                        "rest": rest_amt})
    people = pd.concat(out, ignore_index=True)
    people["grp"] = None
    for g, codes in DEGREE.items():
        people.loc[people.deg.isin(list(codes)), "grp"] = g
    assert people.grp.notna().all(), people[people.grp.isna()].deg.unique()
    return people[people.age >= 25].reset_index(drop=True), fam


def replicate_weights(year, ids):
    r = pd.read_stata(X / f"scf{year}rw1s" / f"p{str(year)[2:]}_rw1.dta")
    r.columns = r.columns.str.lower()   # the 2016 file uses upper case
    r = r.set_index("yy1")
    wt = r[[f"wt1b{k}" for k in range(1, 1000)]].to_numpy() * r[[f"mm{k}" for k in range(1, 1000)]].to_numpy()
    # A missing replicate weight marks a case not drawn in that bootstrap
    # replicate, so it counts as zero.
    rw = pd.DataFrame(np.nan_to_num(wt), index=r.index)
    return rw.loc[ids].to_numpy()


def wmedian(x, w):
    """Weighted median as in MEANIT: first sorted value where the cumulative
    weight share reaches one half. w may be a matrix (one column per weight)."""
    o = np.argsort(x, kind="stable")
    x, w = x[o], w[o]
    c = np.cumsum(w, axis=0) / w.sum(axis=0)
    return x[np.argmax(c >= 0.5, axis=0)]


def stats(df, rw, cpi_f):
    """Point estimates and SEs for one year's persons subset."""
    res = {}
    imps = [df[df.imp == i] for i in range(1, 6)]
    first = df.imp == 1
    W1 = rw[first.to_numpy()]
    d1 = df[first]
    funcs = {
        "has_debt": lambda debt, w: (w * (debt > 0)[:, None] if w.ndim == 2 else w * (debt > 0)).sum(axis=0) / w.sum(axis=0) * 100,
        "median_holders": lambda debt, w: wmedian(debt[debt > 0], w[debt > 0]) * cpi_f,
        "mean_holders": lambda debt, w: ((debt[debt > 0, None] if w.ndim == 2 else debt[debt > 0]) * w[debt > 0]).sum(axis=0)
                                        / w[debt > 0].sum(axis=0) * cpi_f,
        "mean_all": lambda debt, w: ((debt[:, None] if w.ndim == 2 else debt) * w).sum(axis=0) / w.sum(axis=0) * cpi_f,
    }
    for k, fn in funcs.items():
        est = np.array([fn(i.debt.to_numpy(), i.w.to_numpy()) for i in imps])
        reps = fn(d1.debt.to_numpy(), W1)
        iv = est.var(ddof=1)
        rv = ((reps - reps.mean()) ** 2).sum() / 998
        res[k] = est.mean()
        res[k + "_se"] = np.sqrt(6 / 5 * iv + rv)
    res["n"] = int(len(d1))
    res["n_holders"] = int((d1.debt > 0).sum())
    res["pop_m"] = df.w.sum() / 5 / 1e6
    return res


def pay_change():
    """ACS B20004 national median earnings, 2016 and 2025, percent change after inflation."""
    cpi = cpi_annual()
    f = cpi[2025] / cpi[2016]
    med = {}
    for y in YEARS:
        js = json.loads((RAW / str(y) / "B20004_us.json").read_text())
        row = dict(zip(js[0], js[1]))
        med[y] = {g: float(row[f"B20004_00{i}E"]) for i, g in enumerate(["all", "lths", "hs", "somecol", "ba", "grad"], 1)}
    return {g: 100 * (med[2025][g] / (med[2016][g] * f) - 1) for g in med[2016]}, med


def main():
    cpi = cpi_annual()
    rows, alloc = [], []
    for year in YEARS:
        cpi_f = cpi[2025] / cpi[year]
        people, fam = persons(year)
        rw = replicate_weights(year, people.loc[people.imp == 1, "yy1"].to_numpy())
        rw_all = np.full((len(people), 999), np.nan)
        rw_all[(people.imp == 1).to_numpy()] = rw
        for band, lo, hi in (("25+", 25, 200), ("25-39", 25, 39)):
            for g, parts in GROUPS.items():
                m = people.grp.isin(parts) & people.age.between(lo, hi)
                s = stats(people[m].reset_index(drop=True), rw_all[m.to_numpy()], cpi_f)
                rows.append({"year": year, "ages": band, "group": g, **s})
        tot = (fam.w * fam.total).sum() / 5 * cpi_f / 1e9
        bn = {k: (fam.w * fam[k]).sum() / 5 * cpi_f / 1e9 for k in ("assigned", "child", "multiple", "rest")}
        alloc.append({"year": year, "all_student_debt_bn": tot, **{k + "_bn": v for k, v in bn.items()},
                      "assigned_pct": 100 * bn["assigned"] / tot})
    df = pd.DataFrame(rows)
    df.to_csv(CLEAN / "scf_debt.csv", index=False, float_format="%.4f")

    pay, med = pay_change()
    out = ["# Student debt tables (generated by scripts/scf_debt.py)", "",
           f"Survey of Consumer Finances 2016 and 2025. Dollars in 2025 dollars (R-CPI-U-RS, 2016 to 2025: "
           f"prices up {100 * (cpi[2025] / cpi[2016] - 1):.1f}%). Own student debt only: loans for the person's own "
           "education. Standard errors combine imputation and replicate-weight variance (SCF MEANIT). "
           "A change passes if |z| > 1.645 (90% confidence).", "",
           "## Student loan balances assigned to a person", "",
           "| year | all ($bn, 2025$) | own education of reference person or spouse ($bn) | child or other relative ($bn) | "
           "multiple people ($bn) | 7th and later loans ($bn) | share assigned (%) |",
           "|---|---|---|---|---|---|---|"]
    out += [f"| {a['year']} | {a['all_student_debt_bn']:.0f} | {a['assigned_bn']:.0f} | {a['child_bn']:.0f} | "
            f"{a['multiple_bn']:.0f} | {a['rest_bn']:.0f} | {a['assigned_pct']:.1f} |" for a in alloc]
    for band in ("25+", "25-39"):
        out += ["", f"## Ages {band}", "",
                "| group | year | adults (m) | sample persons | with own student debt (%) | ± MOE | median among borrowers ($) | ± MOE | "
                "mean among borrowers ($) | mean per adult ($) |", "|---|---|---|---|---|---|---|---|---|---|"]
        for g in GROUPS:
            for y in YEARS:
                r = df[(df.ages == band) & (df.group == g) & (df.year == y)].iloc[0]
                out.append(f"| {NAMES[g]} | {y} | {r.pop_m:.1f} | {r.n} ({r.n_holders} with debt) | {r.has_debt:.1f} | "
                           f"{Z90 * r.has_debt_se:.1f} | {r.median_holders:,.0f} | {Z90 * r.median_holders_se:,.0f} | "
                           f"{r.mean_holders:,.0f} | {r.mean_all:,.0f} |")
        out += ["", f"### Ages {band}: change 2016 to 2025", "",
                "| group | share with debt (points) | passes | median among borrowers (%) | passes | mean per adult (%) | passes |",
                "|---|---|---|---|---|---|---|"]
        for g in GROUPS:
            a = df[(df.ages == band) & (df.group == g) & (df.year == 2016)].iloc[0]
            b = df[(df.ages == band) & (df.group == g) & (df.year == 2025)].iloc[0]

            def test(k):
                return abs(b[k] - a[k]) / np.hypot(a[k + "_se"], b[k + "_se"]) > Z90
            out.append(f"| {NAMES[g]} | {b.has_debt - a.has_debt:+.1f} | {'yes' if test('has_debt') else 'no'} | "
                       f"{100 * (b.median_holders / a.median_holders - 1):+.1f} | {'yes' if test('median_holders') else 'no'} | "
                       f"{100 * (b.mean_all / a.mean_all - 1):+.1f} | {'yes' if test('mean_all') else 'no'} |")
    out += ["", "## ACS median earnings (B20004), nation, 2016 to 2025, after inflation", "",
            "| group | 2016 ($, 2016$) | 2025 ($) | change after inflation (%) |", "|---|---|---|---|"]
    out += [f"| {'All workers 25 and over' if g == 'all' else NAMES[g]} | {med[2016][g]:,.0f} | {med[2025][g]:,.0f} | {pay[g]:+.1f} |"
            for g in med[2016]]
    (CLEAN / "scf_debt_tables.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
