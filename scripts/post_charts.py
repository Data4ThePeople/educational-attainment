"""Static charts for the post, computed from the data built into
dist/index.html with the map's own share, test and index math (so the
charts match the map). Run after build_viz.py.

Writes posts/educational-attainment/images/01-edu-rise-metros.png,
02-pay-mix-nation.png and data/clean/post_chart_tables.md.
"""
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from mapping import GROUPS, GROUP_NAMES, ROOT  # noqa: E402
from debt_charts import C2016, C2025, GRID, INK2, MUTED, footer, frame  # noqa: E402

IMG = ROOT / "posts" / "educational-attainment" / "images"
Z90 = 1.645
NOPASS = "#cfcdc6"
LEVELS = [("hsplus", "High school or more", ["hs", "somecol", "ba", "grad"]),
          ("scplus", "Some college or more", ["somecol", "ba", "grad"]),
          ("baplus", "Bachelor's degree or more", ["ba", "grad"]),
          ("grad", "Graduate or professional degree", ["grad"])]
OUT = []


def share(r, groups):
    # Handbook ch. 8 formula (6), or (7) when the radicand is negative; same as the map.
    x = sum(r[2 + 2 * GROUPS.index(g)] for g in groups)
    mx2 = sum(r[3 + 2 * GROUPS.index(g)] ** 2 for g in groups)
    y, my = r[0], r[1]
    p = x / y
    rad = mx2 - p * p * my * my
    if rad < 0:
        rad = mx2 + p * p * my * my
    return 100 * p, 100 * np.sqrt(rad) / y


def ztest(a, b):
    return (b[0] - a[0]) / np.sqrt((a[1] / Z90) ** 2 + (b[1] / Z90) ** 2)


def swarm(x, r):
    # Simple beeswarm: place each dot at the smallest |y| that keeps it r away from placed dots.
    ys, placed = np.zeros(len(x)), []
    for i in np.argsort(x):
        near = [(px, py) for px, py in placed if abs(px - x[i]) < 2 * r]
        for k in range(200):
            y = (k + 1) // 2 * r * 0.9 * (1 if k % 2 else -1)
            if all((px - x[i]) ** 2 + (py - y) ** 2 >= (2 * r) ** 2 for px, py in near):
                break
        ys[i] = y
        placed.append((x[i], y))
    return ys


def edu_chart(data, geo, first, last):
    ids = {x["id"] for x in geo["cbsa"]}
    areas = [a for a in data["areas"] if a["id"] in ids and a.get("c") and a["v"].get(first) and a["v"].get(last)]
    OUT.extend([f"## Metro and micro areas, change in share of adults 25 and over, {first} to {last}", "",
                f"{len(areas)} comparable areas (the map's set). Test: Census Bureau z-test at 90% confidence.", "",
                "| level | US change (pts) | areas | rise passes | % | fall passes | point estimate rose | median change (pts) |",
                "|---|---|---|---|---|---|---|---|"])
    h = 8.2
    fig, ax = frame(f"Change in education in metro and micro areas, {first} to {last}",
                    "Change in the share of adults 25 and over, in percentage points. Each dot is one area.", h)
    ax.set_position([0.27, 1.75 / h, 0.58, 1 - 3.4 / h])
    rows = []
    for j, (key, label, groups) in enumerate(LEVELS):
        d, z = [], []
        for a in areas:
            t, n = share(a["v"][first], groups), share(a["v"][last], groups)
            d.append(n[0] - t[0])
            z.append(ztest(t, n))
        d, z = np.array(d), np.array(z)
        us = share(data["us"][last], groups)[0] - share(data["us"][first], groups)[0]
        up = int((z > Z90).sum())
        rows.append((label, up, len(d), np.median(d)))
        OUT.append(f"| {label} | {us:+.2f} | {len(d)} | {up} | {100 * up / len(d):.1f} | {int((z < -Z90).sum())} | "
                   f"{int((d > 0).sum())} | {np.median(d):+.2f} |")
        y0 = len(LEVELS) - 1 - j
        ys = y0 + swarm(d, 0.034)
        sig = z > Z90
        ax.scatter(d[~sig], ys[~sig], s=13, color=NOPASS, edgecolor="none", zorder=2)
        ax.scatter(d[sig], ys[sig], s=13, color=C2025, edgecolor="none", zorder=3)
        ax.text(1.03, y0 + 0.08, f"{100 * up / len(d):.0f}%", ha="left", va="center", fontsize=16, fontweight="bold",
                color=C2025, transform=ax.get_yaxis_transform())
        ax.text(1.03, y0 - 0.16, "passed the test", ha="left", va="center", fontsize=10, color=INK2,
                transform=ax.get_yaxis_transform())
    ax.axvline(0, color=INK2, lw=1, zorder=1)
    ax.set_yticks(range(len(LEVELS)))
    ax.set_yticklabels([lab for _, lab, _ in reversed(LEVELS)])
    ax.set_xlim(-6, 18)
    ax.set_ylim(-0.55, len(LEVELS) - 0.45)
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+.0f}".replace("-", "−") if v else "0"))
    ax.set_xlabel("Change in percentage points", fontsize=11, color=INK2, labelpad=8)
    ax.scatter([], [], s=40, color=C2025, label="Rise passes the Census Bureau's test")
    ax.scatter([], [], s=40, color=NOPASS, label="Change does not pass the test")
    ax.legend(loc="lower left", bbox_to_anchor=(-0.4, 1.02), ncol=2, frameon=False, fontsize=10.5, handletextpad=0.2,
              borderaxespad=0)
    footer(fig, f"Source: U.S. Census Bureau, American Community Survey 1-year estimates, table B15003. {len(areas)} metro "
           f"and micro areas with comparable {first} and {last} boundaries. Tests use 90% confidence. Part of the rise "
           f"in high school or more and some college or more may come from the {last} survey changes.", h)
    fig.savefig(IMG / "01-edu-rise-metros.png", facecolor="white")
    plt.close(fig)
    return rows


def pay_chart(data, first, last):
    f = data["cpi"][last] / data["cpi"][first]
    e1 = [x * f for x in data["usPay"][first]]
    e2 = data["usPay"][last]
    w1, w2 = data["us"][first], data["us"][last]

    def pct(i):
        a, b, ma, mb = e1[2 * i], e2[2 * i], e1[2 * i + 1], e2[2 * i + 1]
        return 100 * (b / a - 1), abs(b - a) / np.sqrt((ma / Z90) ** 2 + (mb / Z90) ** 2) > Z90

    def index(e, w):
        return sum(w[2 + 2 * i] / w[0] * e[2 + 2 * i] for i in range(len(GROUPS)))

    h1, h2, o2 = index(e1, w1), index(e2, w1), index(e2, w2)
    within, mix = 100 * (h2 / h1 - 1), 100 * (o2 - h2) / h1
    groups = [(GROUP_NAMES[g], *pct(i + 1)) for i, g in enumerate(GROUPS)]
    allw = pct(0)
    OUT.extend(["", f"## Nation, pay {first} to {last}, total change after inflation ({last} dollars)", "",
                f"Prices up {100 * (f - 1):.1f}%.", "", "| measure | change (%) | passes |", "|---|---|---|"])
    OUT.extend(f"| Median, {n} | {v:+.2f} | {s} |" for n, v, s in groups)
    OUT.extend([f"| Median, all workers | {allw[0]:+.2f} | {allw[1]} |",
                f"| Pay index, total ({first} index ${h1:,.0f}, {last} ${o2:,.0f}) | {100 * (o2 / h1 - 1):+.2f} | |",
                f"| From pay within education groups ({last} index with {first} mix ${h2:,.0f}) | {within:+.2f} | |",
                f"| From the education mix (points) | {mix:+.2f} | |"])

    h = 7.0
    fig, ax = frame(f"Change in median pay by education, {first} to {last}",
                    "Percent change after inflation, adults 25 and over with earnings, United States", h)
    ax.set_position([0.31, 1.45 / h, 0.62, 1 - 2.95 / h])
    labels = [n for n, _, _ in groups] + ["All workers", "Pay index"]
    n = len(labels)
    ys = list(range(n - 1, -1, -1))
    ys = [y + (0 if i < len(groups) else -0.5) for i, y in enumerate(ys)]

    def lab(y, x, text):
        ax.text(x + 0.3 if x >= 0 else 0.3, y, text, ha="left", va="center", fontsize=11, color=INK2)

    for (name, v, s), y in zip(groups, ys):
        ax.barh(y, v, height=0.6, color=C2016 if s else NOPASS, zorder=2)
        lab(y, v, f"{v:+.1f}%".replace("-", "−") + ("" if s else " (does not pass the test)"))
    ax.barh(ys[-2], allw[0], height=0.6, color=C2025, zorder=2)
    lab(ys[-2], allw[0], f"{allw[0]:+.1f}%")
    ax.barh(ys[-1], within, height=0.75, color=C2025, zorder=2)
    ax.barh(ys[-1], mix, left=within, height=0.75, color="#4f8fd9", zorder=2, edgecolor="white", linewidth=2)
    lab(ys[-1], within + mix, f"{within + mix:+.1f}%")
    ax.text(within / 2, ys[-1], f"Pay within\ngroups {within:+.1f}", ha="center", va="center", fontsize=9, color="white")
    ax.text(within + mix / 2, ys[-1], f"Education\nmix {mix:+.1f}", ha="center", va="center", fontsize=9, color="white")
    ax.axhline((ys[len(groups) - 1] + ys[-2]) / 2, color=GRID, lw=1)
    ax.axvline(0, color=INK2, lw=1)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels)
    ax.set_xlim(-2, 24)
    ax.set_ylim(min(ys) - 0.6, max(ys) + 0.6)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+.0f}%".replace("-", "−") if v else "0%"))
    footer(fig, f"Source: U.S. Census Bureau, American Community Survey 1-year, tables B20004 (median earnings) and B15003 "
           f"(education). {first} dollars moved to {last} dollars with the BLS R-CPI-U-RS. The pay index weights each "
           f"group's median pay by its share of all adults 25 and over. It is an index, not a median. The education mix "
           f"part is in percentage points.", h)
    fig.savefig(IMG / "02-pay-mix-nation.png", facecolor="white")
    plt.close(fig)


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    html = (ROOT / "dist" / "index.html").read_text()
    data = json.loads(re.search(r"const DATA = (\{.*?\});\n", html).group(1))
    geo = json.loads(re.search(r"const GEO = (\{.*?\});\n", html).group(1))
    first, last = str(data["first"]), str(data["last"])
    OUT.extend(["# Post chart tables (generated by scripts/post_charts.py)", ""])
    edu_chart(data, geo, first, last)
    pay_chart(data, first, last)
    (ROOT / "data" / "clean" / "post_chart_tables.md").write_text("\n".join(OUT) + "\n")
    print("\n".join(OUT))


if __name__ == "__main__":
    main()
