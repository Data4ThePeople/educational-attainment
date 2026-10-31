"""Static charts for the student debt part of the story, from
data/clean/scf_debt.csv (scripts/scf_debt.py) and the ACS B20004 national
medians. Writes PNGs to dist/charts/. Run after scf_debt.py.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from mapping import ROOT  # noqa: E402
from scf_debt import NAMES, Z90, pay_change  # noqa: E402

OUT = ROOT / "dist" / "charts"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#77756f", "#e1e0d9"
C2016, C2025 = "#9ec5f4", "#184f95"          # map ramp steps b2 and b6
SHOWN = ["somecol", "ba", "ma", "prof"]
SOURCE = ("Source: Federal Reserve Board, Survey of Consumer Finances 2016 and 2025. Own student debt: loans for the "
          "person's own education, for each family's reference person and spouse or partner, ages 25 and over. "
          "Lines show 90% margins of error.")
plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 13, "text.color": INK,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK})


def frame(title, subtitle, h=6.2):
    fig = plt.figure(figsize=(10.4, h), dpi=150)
    fig.text(0.04, 0.95, title, fontsize=19, fontweight="bold", va="top")
    fig.text(0.04, 0.95 - 0.55 / h, subtitle, fontsize=13, color=INK2, va="top")
    ax = fig.add_axes([0.27, 1.55 / h, 0.68, 1 - 3.0 / h])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    return fig, ax


def footer(fig, text, h):
    fig.text(0.04, 0.55 / h, text, fontsize=9.5, color=MUTED, va="bottom", wrap=True)
    fig.text(0.04, 0.2 / h, "Built by Data 4 The People", fontsize=9.5, color=MUTED, va="bottom", fontweight="bold")


def dumbbell(d, key, title, subtitle, fmt, name, xmax):
    h = 6.2
    fig, ax = frame(title, subtitle, h)
    for i, g in enumerate(SHOWN):
        y = len(SHOWN) - 1 - i
        a = d[(d.group == g) & (d.year == 2016)].iloc[0]
        b = d[(d.group == g) & (d.year == 2025)].iloc[0]
        ax.plot([a[key], b[key]], [y, y], color=GRID, lw=3, zorder=1, solid_capstyle="round")
        for r, c, dy in ((a, C2016, 0.13), (b, C2025, -0.13)):
            m = Z90 * r[key + "_se"]
            ax.plot([r[key] - m, r[key] + m], [y + dy, y + dy], color=c, lw=2, zorder=2, solid_capstyle="round")
            ax.scatter(r[key], y + dy, s=110, color=c, edgecolor="white", linewidth=2, zorder=3)
        right = max(r[key] + Z90 * r[key + "_se"] for r in (a, b))
        ax.text(right + xmax * 0.015, y + 0.13, f"2016: {fmt(a[key])}", ha="left", va="center", fontsize=11.5, color=INK2)
        ax.text(right + xmax * 0.015, y - 0.13, f"2025: {fmt(b[key])}", ha="left", va="center", fontsize=11.5, color=INK2)
    ax.set_yticks(range(len(SHOWN)))
    ax.set_yticklabels([NAMES[g] for g in reversed(SHOWN)])
    ax.set_xlim(0, xmax)
    ax.set_ylim(-0.6, len(SHOWN) - 0.4)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: fmt(v)))
    footer(fig, SOURCE, h)
    fig.savefig(OUT / name, facecolor="white")
    plt.close(fig)


def change_bars(d, pay):
    h = 5.4
    fig, ax = frame("Pay and student debt by degree, 2016 to 2025",
                    "Percent change after inflation: median pay of workers, and median own student debt of borrowers", h)
    rows = [("ba", "ba"), ("grad", "grad")]
    debt = {g: 100 * (d[(d.group == g) & (d.year == 2025)].iloc[0].median_holders /
                      d[(d.group == g) & (d.year == 2016)].iloc[0].median_holders - 1) for g, _ in rows}
    for i, (g, pg) in enumerate(rows):
        y = len(rows) - 1 - i
        for v, c, dy, lab in ((pay[pg], C2016, 0.17, "Median pay"), (debt[g], C2025, -0.17, "Median student debt")):
            ax.barh(y + dy, v, height=0.3, color=c, zorder=2)
            ax.text(v + (0.4 if v >= 0 else -0.4), y + dy, f"{lab}: {v:+.1f}%".replace("-", "\u2212"), ha="left" if v >= 0 else "right",
                    va="center", fontsize=11.5, color=INK2)
    ax.axvline(0, color=INK2, lw=1)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([NAMES[g] for g, _ in reversed(rows)])
    ax.set_xlim(-16, 16)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+.0f}%".replace("-", "\u2212") if v else "0%"))
    footer(fig, "Sources: U.S. Census Bureau, American Community Survey 1-year, table B20004 (median earnings of people 25 "
           "and over with earnings); Federal Reserve Board, Survey of Consumer Finances (median own student debt among "
           "borrowers 25 and over). 2016 dollars moved to 2025 dollars with the BLS R-CPI-U-RS. Neither debt change passes "
           "a test at 90% confidence.", h)
    fig.savefig(OUT / "debt_vs_pay_change.png", facecolor="white")
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ROOT / "data" / "clean" / "scf_debt.csv")
    d = d[d.ages == "25+"]
    dumbbell(d, "has_debt", "Adults with student debt for their own education, 2016 and 2025",
             "Percent of adults 25 and over, by highest degree", lambda v: f"{v:.0f}%", "debt_share.png", 36)
    dumbbell(d, "median_holders", "Median student debt among borrowers, 2016 and 2025",
             "Own student debt of borrowers 25 and over, by highest degree, in 2025 dollars",
             lambda v: f"${v / 1000:.0f}k", "debt_median.png", 200000)
    pay, _ = pay_change()
    change_bars(d, pay)
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
