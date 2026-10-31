"""Student debt per borrower from credit reports (New York Fed Consumer
Credit Panel / Equifax), nation and states, after inflation.

Files (data/raw/nyfed/, from the New York Fed Center for Microeconomic Data
data bank):
- student-loan-update-2025-mangrum.xlsx: national median and average balance
  per borrower, 2004-2024 (Page 8), and borrowers, average and median balance
  by state, 2019Q4-2024Q4 (Pages 9-14).
- student-loan-by-state.xlsx: borrowers and average balance by state,
  2016-2021 (year end). Its 2019-2021 averages match the update file to within
  0.2%, so 2016 comes from this file.

Dollars are moved to 2025 dollars with the R-CPI-U-RS annual averages
(build_viz.cpi_annual). Writes data/clean/credit_debt_us.csv,
data/clean/credit_debt_state.csv and charts in dist/charts/.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from mapping import RAW, ROOT  # noqa: E402
from build_viz import cpi_annual  # noqa: E402
from debt_charts import C2016, C2025, GRID, INK2, MUTED, OUT, footer, frame  # noqa: E402

NYFED = RAW / "nyfed"
CLEAN = ROOT / "data" / "clean"
FIRST, LAST = 2016, 2024
SRC = ("Source: Federal Reserve Bank of New York Consumer Credit Panel / Equifax (student loans, federal and private, "
       "for borrowers with a balance at year end). 2025 dollars using the BLS R-CPI-U-RS.")


def us_series():
    p = pd.read_excel(NYFED / "student-loan-update-2025-mangrum.xlsx", header=None, sheet_name="Page 8")
    hdr = p.index[p[2].astype(str).str.strip() == "25th percentile balance"][0]
    assert str(p.iat[hdr, 3]).strip() == "median balance" and str(p.iat[hdr, 5]).strip() == "average balance"
    rows = p.iloc[hdr + 1:]
    rows = rows[pd.to_numeric(rows[0], errors="coerce").notna()]
    return pd.DataFrame({"year": rows[0].astype(int), "median": rows[3].astype(float),
                         "average": rows[5].astype(float)}).reset_index(drop=True)


def state_new(year):
    page = {2019: 9, 2020: 10, 2021: 11, 2022: 12, 2023: 13, 2024: 14}[year]
    p = pd.read_excel(NYFED / "student-loan-update-2025-mangrum.xlsx", header=None, sheet_name=f"Page {page}")
    assert f"({year}Q4)" in str(p.iat[4, 0])
    hdr = p.index[p[0].astype(str).str.strip() == "State"][0]
    assert [str(v).strip() for v in p.iloc[hdr, 1:5]] == ["Total Borrowers", "Total Balance (Billions)",
                                                          "Average Balance", "Median Balance"]
    rows = p.iloc[hdr + 1:]
    rows = rows[pd.to_numeric(rows[1], errors="coerce").notna()]
    out = pd.DataFrame({"state": rows[0].str.strip().str.replace("District Of Columbia", "District of Columbia"),
                        "borrowers": rows[1].astype(float), "average": rows[3].astype(float),
                        "median": rows[4].astype(float)})
    assert out.state.is_unique
    return out.set_index("state")


def state_old(year):
    p = pd.read_excel(NYFED / "student-loan-by-state.xlsx", header=None, sheet_name="average borrower bal by state")
    hdr = p.index[p[0].astype(str).str.strip() == "state/area"][0]
    col = [c for c in p.columns if str(p.iat[hdr, c]).strip() in (str(year), f"{year}.0")]
    assert len(col) == 1
    rows = p.iloc[hdr + 1:]
    rows = rows[pd.to_numeric(rows[col[0]], errors="coerce").notna()]
    s = pd.Series(rows[col[0]].astype(float).values, index=rows[0].str.strip(), name="average")
    assert s.index.is_unique
    return s


def main():
    cpi = cpi_annual()
    f = {y: cpi[2025] / cpi[y] for y in cpi}
    us = us_series()
    us["median_2025usd"] = us.apply(lambda r: r["median"] * f[r.year], axis=1)
    us["average_2025usd"] = us.apply(lambda r: r["average"] * f[r.year], axis=1)
    us.to_csv(CLEAN / "credit_debt_us.csv", index=False, float_format="%.0f")

    # Overlap check between the two state files.
    for y in (2019, 2020, 2021):
        o, n = state_old(y), state_new(y).average
        j = pd.concat([o, n], axis=1, join="inner").dropna()
        assert len(j) >= 51 and ((j.iloc[:, 1] / j.iloc[:, 0] - 1).abs() < 0.005).all(), y
    a, b = state_old(FIRST), state_new(LAST)
    st = pd.DataFrame({"avg_first": a, "avg_last": b.average, "borrowers_last": b.borrowers})
    # The update file has no United States row; use the national series
    # (Page 8), which matches the older file's United States row in 2016 to
    # within rounding.
    nat = us.set_index("year").average
    assert abs(nat[FIRST] / st.at["United States", "avg_first"] - 1) < 0.005
    st.at["United States", "avg_first"] = nat[FIRST]
    st.at["United States", "avg_last"] = nat[LAST]
    st = st.dropna(subset=["avg_first", "avg_last"])
    st["avg_first_2025usd"] = st.avg_first * f[FIRST]
    st["avg_last_2025usd"] = st.avg_last * f[LAST]
    st["change_pct"] = 100 * (st.avg_last_2025usd / st.avg_first_2025usd - 1)
    assert "United States" in st.index and len(st) >= 52, len(st)
    st.sort_values("change_pct").to_csv(CLEAN / "credit_debt_state.csv", float_format="%.2f")

    lines = ["# Credit report student debt (generated by scripts/credit_debt.py)", "",
             f"2025 dollars, R-CPI-U-RS. Prices up {100 * (f[FIRST] - 1):.1f}% from {FIRST} to 2025 and "
             f"{100 * (f[LAST] - 1):.1f}% from {LAST} to 2025.", "",
             "## Nation, per borrower", "", "| year | median ($) | average ($) | median, 2025$ | average, 2025$ |",
             "|---|---|---|---|---|"]
    lines += [f"| {int(r.year)} | {r['median']:,.0f} | {r.average:,.0f} | {r.median_2025usd:,.0f} | {r.average_2025usd:,.0f} |"
              for _, r in us.iterrows()]
    g = us.set_index("year")
    for y0 in (2015, 2016):
        lines.append(f"\n{y0} to {LAST}, after inflation: median {100 * (g.median_2025usd[LAST] / g.median_2025usd[y0] - 1):+.1f}%, "
                     f"average {100 * (g.average_2025usd[LAST] / g.average_2025usd[y0] - 1):+.1f}%.")
    lines += ["", f"## States, average balance per borrower, {FIRST} to {LAST}, after inflation", "",
              f"| state | {FIRST} (2025$) | {LAST} (2025$) | change (%) |", "|---|---|---|---|"]
    lines += [f"| {s} | {r.avg_first_2025usd:,.0f} | {r.avg_last_2025usd:,.0f} | {r.change_pct:+.1f} |"
              for s, r in st.sort_values("change_pct", ascending=False).iterrows()]
    sts = st.drop("United States")
    lines += ["", f"States and areas with a rise: {(sts.change_pct > 0).sum()} of {len(sts)}; "
              f"median change {sts.change_pct.median():+.1f}%."]
    (CLEAN / "credit_debt_tables.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[-8:]))

    # Chart 1: national median and average per borrower, 2025 dollars.
    h = 6.0
    fig, ax = frame("Student debt per borrower, 2004 to 2024",
                    "Median and average balance among people with student loans, in 2025 dollars", h)
    ax.set_position([0.08, 1.55 / h, 0.80, 1 - 3.0 / h])
    for col, c, lab in (("average_2025usd", C2025, "Average"), ("median_2025usd", C2016, "Median")):
        ax.plot(us.year, us[col], color=c, lw=2.5)
        ax.text(us.year.iloc[-1] + 0.3, us[col].iloc[-1], f"{lab}\n${us[col].iloc[-1] / 1000:.1f}k", va="center",
                fontsize=11.5, color=INK2)
        v15 = g[col][2015]
        ax.scatter([2015], [v15], s=50, color=c, edgecolor="white", linewidth=1.5, zorder=3)
        dy = 2600 if col == "average_2025usd" else -3600
        ax.text(2015, v15 + dy, f"2015: ${v15 / 1000:.1f}k", ha="center", fontsize=10.5, color=INK2)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.grid(axis="x", visible=False)
    ax.set_xlim(2004, LAST)
    ax.set_ylim(0, 55000)
    ax.set_xticks(range(2004, LAST + 1, 4))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"${v / 1000:.0f}k" if v else "$0"))
    ax.tick_params(axis="x", pad=8)
    footer(fig, SRC, h)
    fig.savefig(OUT / "credit_debt_per_borrower_us.png", facecolor="white")
    plt.close(fig)

    # Chart 2: states ranked by change in average balance per borrower.
    s = st.sort_values("change_pct")
    h = 13.5
    fig, ax = frame(f"Change in average student debt per borrower, {FIRST} to {LAST}",
                    "After inflation, by state of the borrower's mailing address", h)
    ax.set_position([0.25, 1.4 / h, 0.68, 1 - 3.0 / h])
    ys = range(len(s))
    colors = [C2025 if n == "United States" else C2016 for n in s.index]
    ax.barh(list(ys), s.change_pct, color=colors, height=0.7)
    ax.axvline(0, color=INK2, lw=1)
    ax.set_yticks(list(ys))
    ax.set_yticklabels(s.index, fontsize=9.5)
    for y, (n, r) in zip(ys, s.iterrows()):
        ax.text(r.change_pct + (0.3 if r.change_pct >= 0 else -0.3), y, f"{r.change_pct:+.1f}%".replace("-", "−"),
                va="center", ha="left" if r.change_pct >= 0 else "right", fontsize=8.5, color=MUTED)
    lim = max(abs(s.change_pct)) + 4
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-0.7, len(s) - 0.3)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+.0f}%".replace("-", "−") if v else "0%"))
    footer(fig, SRC + " Average balance among borrowers at year end. The United States bar is dark blue.", h)
    fig.savefig(OUT / "credit_debt_change_by_state.png", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
