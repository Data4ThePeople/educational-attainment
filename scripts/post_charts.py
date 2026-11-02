"""Static charts for the post, computed from the data built into
dist/index.html with the map's own share, test and index math (so the
charts match the map). Run after build_viz.py.

Writes posts/educational-attainment/images/01-edu-rise-metros.png,
02-coffee-bridge.png, 03-pay-mix-nation.png, 04-pay-mix-metros.png,
educational-attainment-hero-source.png (the national pay index as a bridge,
drawn at the hero's 1680 x 1080 and copied by ~/.claude/d4tp-process/hero fit) and
data/clean/post_chart_tables.md. Chart 4 reads data/clean/pay_change.csv
(scripts/pay_findings.py), which uses the same data.
The coffee shop chart uses the made-up numbers from the post's example.
"""
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from mapping import GROUPS, GROUP_NAMES, ROOT  # noqa: E402
from debt_charts import C2016, C2025, GRID, INK2, MUTED, footer, frame  # noqa: E402

IMG = ROOT / "posts" / "educational-attainment" / "images"
Z90 = 1.645
NOPASS = "#cfcdc6"
FALL = "#c2552d"
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

    n_yrs = int(last) - int(first)

    def cagr(a, b):
        return 100 * ((b / a) ** (1 / n_yrs) - 1)

    def pct(i):
        a, b, ma, mb = e1[2 * i], e2[2 * i], e1[2 * i + 1], e2[2 * i + 1]
        return cagr(a, b), abs(b - a) / np.sqrt((ma / Z90) ** 2 + (mb / Z90) ** 2) > Z90

    def index(e, w):
        return sum(w[2 + 2 * i] / w[0] * e[2 + 2 * i] for i in range(len(GROUPS)))

    # Same split as the map: own-mix yearly change = held-mix yearly change + mix part (points).
    h1, h2, o2 = index(e1, w1), index(e2, w1), index(e2, w2)
    within, total = cagr(h1, h2), cagr(h1, o2)
    mix = total - within
    groups = [(GROUP_NAMES[g], *pct(i + 1)) for i, g in enumerate(GROUPS)]
    allw = pct(0)
    OUT.extend(["", f"## Nation, pay {first} to {last}, yearly change after inflation ({last} dollars)", "",
                f"Prices up {100 * (f - 1):.1f}%. Yearly change is the compound annual growth rate over {n_yrs} years.", "",
                "| measure | yearly change (%) | passes |", "|---|---|---|"])
    OUT.extend(f"| Median, {n} | {v:+.2f} | {s} |" for n, v, s in groups)
    OUT.extend([f"| Median, all workers | {allw[0]:+.2f} | {allw[1]} |",
                f"| Pay index, total ({first} index ${h1:,.0f}, {last} ${o2:,.0f}) | {total:+.2f} | |",
                f"| From pay within education groups ({last} index with {first} mix ${h2:,.0f}) | {within:+.2f} | |",
                f"| From the education mix (points a year) | {mix:+.2f} | |"])

    h = 6.6
    fig, ax = frame(f"Yearly change in median pay by education, {first} to {last}",
                    "Percent change a year after inflation, adults 25 and over with earnings, United States, in 2025 dollars", h)
    ax.set_position([0.27, 1.45 / h, 0.50, 1 - 2.95 / h])
    labels = [n for n, _, _ in groups] + ["Pay index"]
    n = len(labels)
    ys = list(range(n - 1, -1, -1))
    ys = [y + (0 if i < len(groups) else -0.5) for i, y in enumerate(ys)]

    def lab(y, x, text):
        ax.text(x + 0.03 if x >= 0 else 0.03, y, text, ha="left", va="center", fontsize=11, color=INK2)

    for (name, v, s), y in zip(groups, ys):
        ax.barh(y, v, height=0.6, color=C2016 if s else NOPASS, zorder=2)
        lab(y, v, f"{v:+.2f}%".replace("-", "\u2212") + ("" if s else " (does not pass the test)"))
    ax.barh(ys[-1], within, height=0.75, color=C2025, zorder=2)
    ax.barh(ys[-1], mix, left=within, height=0.75, color="#4f8fd9", zorder=2, edgecolor="white", linewidth=2)
    lab(ys[-1], total, f"{total:+.2f}%")
    ax.text(within / 2, ys[-1], f"Pay within\ngroups {within:+.2f}", ha="center", va="center", fontsize=9, color="white")
    ax.text(within + mix / 2, ys[-1], f"Education\nmix {mix:+.2f}", ha="center", va="center", fontsize=9, color="white")
    ax.axhline((ys[len(groups) - 1] + ys[-1]) / 2, color=GRID, lw=1)
    ax.axvline(0, color=INK2, lw=1)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels)
    ax.set_xlim(-0.2, 2.4)
    # Start and end values in 2025 dollars, in a column right of the bars.
    t = ax.get_yaxis_transform()
    dollars = [(e1[2 * (i + 1)], e2[2 * (i + 1)]) for i in range(len(GROUPS))] + [(h1, o2)]
    for xc, yr in ((1.17, first), (1.38, last)):
        ax.text(xc, max(ys) + 0.75, yr, ha="right", va="center", fontsize=10.5, color=INK2, fontweight="bold", transform=t)
    for y, (a, b) in zip(ys, dollars):
        for xc, v in ((1.17, a), (1.38, b)):
            ax.text(xc, y, f"\\${v:,.0f}", ha="right", va="center", fontsize=11, color=INK2, transform=t)
    ax.set_ylim(min(ys) - 0.6, max(ys) + 0.9)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+.1f}%".replace("-", "\u2212") if v else "0%"))
    footer(fig, f"Source: U.S. Census Bureau, American Community Survey 1-year, tables B20004 (median earnings) and B15003 "
           f"(education). {first} dollars moved to {last} dollars with the BLS R-CPI-U-RS; the columns on the right show both years in {last} dollars. Yearly change is the compound "
           f"annual growth rate over {n_yrs} years. The pay index weights each group's median pay by its share of all "
           f"adults 25 and over. It is an index, not a median. The education mix part is in percentage points a year.", h)
    fig.savefig(IMG / "03-pay-mix-nation.png", facecolor="white")
    plt.close(fig)
    return h1, h2, o2


def coffee_chart():
    # The post's example: (units, price) last year and this year, drip coffee then the latte.
    last_yr, this_yr = [(5000, 2.00), (6000, 12.00)], [(3000, 2.50), (8000, 12.50)]
    r1 = sum(u * p for u, p in last_yr)
    r2 = sum(u * p for u, p in this_yr)
    units1, units2 = sum(u for u, _ in last_yr), sum(u for u, _ in this_yr)
    avg1 = r1 / units1
    volume = (units2 - units1) * avg1
    price = sum(u1 * (p2 - p1) for (u1, p1), (_, p2) in zip(last_yr, this_yr))
    mix = r2 - r1 - volume - price
    OUT.extend(["", "## Coffee shop example", "", f"Revenue {r1:,.0f} to {r2:,.0f}; volume {volume:+,.0f}; price {price:+,.0f}; "
                f"mix (the rest) {mix:+,.0f}."])
    assert (r1, r2, volume, price, mix) == (82000, 107500, 0, 5500, 20000)

    h = 6.0
    fig, ax = frame("Coffee shop revenue, last year to this year", "The $25,500 rise in revenue, split into volume, price and mix", h)
    ax.set_position([0.08, 1.35 / h, 0.86, 1 - 2.85 / h])
    steps = [("Last year", 0, r1, C2025), ("Volume", r1, volume, C2016), ("Price", r1 + volume, price, C2016),
             ("Mix", r1 + volume + price, mix, C2016), ("This year", 0, r2, C2025)]
    for x, (name, base, v, c) in enumerate(steps):
        ax.bar(x, v, bottom=base, width=0.6, color=c, zorder=2)
        top = base + v
        total = name in ("Last year", "This year")
        ax.text(x, top + 1500, f"${v:,.0f}" if total else f"+${v:,.0f}", ha="center", va="bottom", fontsize=12,
                color=INK2, fontweight="bold" if total else "normal")
        if x < len(steps) - 1:
            ax.plot([x + 0.3, x + 0.7], [top, top], color=MUTED, lw=1, zorder=1)
    ax.set_xticks(range(len(steps)))
    ax.set_xticklabels([n for n, *_ in steps])
    ax.set_ylim(0, 120000)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"${v / 1000:.0f}k" if v else "$0"))
    ax.tick_params(axis="x", pad=8)
    footer(fig, "Made-up numbers for the example in this post. Volume: the shop sold 11,000 drinks in both years. Price: "
           "the $0.50 price increase applied to last year's sales. Mix: the rest of the change, from selling more of the "
           "higher-priced drink.", h)
    fig.savefig(IMG / "02-coffee-bridge.png", facecolor="white")
    plt.close(fig)


def hero_chart(h1, h2, o2, first, last):
    # The coffee shop bridge with the national pay index. The weights are shares that sum to 1 in both
    # years, so there is no volume step: price is pay within groups at the first-year mix, mix is the rest.
    within, mix = h2 - h1, o2 - h2
    OUT.extend(["", f"## Hero: national pay index bridge, {first} to {last} ({last} dollars)", "",
                f"Pay index {h1:,.0f} to {o2:,.0f} ({o2 - h1:+,.0f}); from pay within education groups {within:+,.0f}; "
                f"from the education mix {mix:+,.0f}."])
    assert abs(within + mix - (o2 - h1)) < 1e-6 and within > 0 and mix > 0

    # Drawn at hero size (1680 x 1080) with a takeaway headline, so the type stays large.
    fig = plt.figure(figsize=(11.2, 7.2), dpi=150)
    fig.text(0.06, 0.92, "About half of the rise in the U.S. pay index\nlines up with more education", fontsize=30,
             fontweight="bold", va="top", linespacing=1.15)
    fig.text(0.06, 0.765, f"Pay index after inflation, {first} to {last}, in {last} dollars", fontsize=17, color=INK2, va="top")
    ax = fig.add_axes([0.06, 0.19, 0.88, 0.48])
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0)
    rise = o2 - h1
    steps = [(f"{first}", 0, h1, C2025, f"\\${h1:,.0f}"),
             ("Pay within\neducation groups", h1, within, C2016, f"+\\${within:,.0f} ({100 * within / rise:.0f}%)"),
             ("Education mix", h2, mix, "#4f8fd9", f"+\\${mix:,.0f} ({100 * mix / rise:.0f}%)"),
             (f"{last}", 0, o2, C2025, f"\\${o2:,.0f}")]
    for x, (name, base, v, c, text) in enumerate(steps):
        ax.bar(x, v, bottom=base, width=0.62, color=c, zorder=2)
        top = base + v
        ax.text(x, top + 1500, text, ha="center", va="bottom", fontsize=19, color=INK2,
                fontweight="bold" if base == 0 else "normal")
        if x < len(steps) - 1:
            ax.plot([x + 0.31, x + 0.69], [top, top], color=MUTED, lw=1.2, zorder=1)
    ax.set_xticks(range(len(steps)))
    ax.set_xticklabels([n for n, *_ in steps], fontsize=17, color=INK2)
    ax.set_yticks([])
    ax.set_ylim(0, 66000)
    ax.tick_params(axis="x", pad=10)
    fig.text(0.06, 0.035, f"Source: U.S. Census Bureau, American Community Survey 1-year, tables B20004 and B15003. "
             f"Adults 25 and over.", fontsize=11, color=MUTED, va="bottom")
    fig.text(0.94, 0.035, "Data 4 The People", fontsize=13, color=INK2, fontweight="bold", ha="right", va="bottom")
    fig.savefig(IMG / "educational-attainment-hero-source.png", facecolor="white")
    plt.close(fig)


def pay_metro_chart(first, last):
    d = pd.read_csv(ROOT / "data" / "clean" / "pay_change.csv")
    d = d[d.level == "cbsa"]
    n_all = len(d)
    # Only areas where both parts pass their tests (the mix part's test is approximate).
    d = d[d.held_sig & d.mix_sig]
    x, y = d.held_cagr.to_numpy(), d.mix_part.to_numpy()
    quad = {"both rose": int(((x > 0) & (y > 0)).sum()), "pay fell, mix rose": int(((x < 0) & (y > 0)).sum()),
            "pay rose, mix fell": int(((x > 0) & (y < 0)).sum()), "both fell": int(((x < 0) & (y < 0)).sum())}
    OUT.extend(["", f"## Metro and micro areas, pay index split, yearly change {first} to {last}", "",
                f"{len(d)} of {n_all} comparable areas where both parts pass their tests, from data/clean/pay_change.csv. "
                f"x = from pay within education groups (% a year), y = from the change in education mix (points a year).", "",
                "| quadrant | areas |", "|---|---|"])
    OUT.extend(f"| {k} | {v} |" for k, v in quad.items())
    OUT.append(f"| mix part larger than pay part | {int((y > x).sum())} |")
    OUT.extend(["", "| area | median pay, all workers (%/yr) | pay index (%/yr) | from pay within groups (%/yr) | "
                "from education mix (pts/yr) |", "|---|---|---|---|---|"])
    OUT.extend(f"| {r['name']} | {r.all_cagr:+.2f} | {r.own_cagr:+.2f} | {r.held_cagr:+.2f} | {r.mix_part:+.2f} |"
               for _, r in d.sort_values("held_cagr").iterrows())

    h = 7.9
    fig, ax = frame(f"Pay index growth in metro and micro areas, {first} to {last}",
                    f"Yearly change after inflation, split into its two parts. Each dot is one of the {len(d)} areas "
                    f"where both parts pass the test.", h)
    ax.set_position([0.11, 1.85 / h, 0.84, 1 - 3.35 / h])
    ax.axvline(0, color=INK2, lw=1, zorder=1)
    ax.plot([0, 0.9], [0, 0.9], color=MUTED, lw=1, ls=(0, (4, 3)), zorder=1)
    ax.text(0.92, 0.9, "Both parts equal", ha="left", va="center", fontsize=10, color=MUTED)
    ax.scatter(x, y, s=34, color=C2025, alpha=0.7, edgecolor="white", linewidth=0.6, zorder=2)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.text(3.3, 0.93, f"Both parts rose: {quad['both rose']} areas", ha="right", va="center", fontsize=10.5, color=INK2)
    ax.text(-1.25, 0.93, f"Pay within groups fell,\neducation mix rose: {quad['pay fell, mix rose']} areas", ha="left",
            va="center", fontsize=10.5, color=INK2)
    for name, short, dx, dy, ha in (("New York-Newark", "New York", 0.06, 0.02, "left"),
                                    ("Indianapolis", "Indianapolis", -0.07, 0.05, "right"),
                                    ("Twin Falls", "Twin Falls, ID", 0, -0.04, "center")):
        r = d[d.name.str.startswith(name)].iloc[0]
        ax.scatter([r.held_cagr], [r.mix_part], s=60, facecolor="none", edgecolor=INK2, linewidth=1.4, zorder=3)
        ax.text(r.held_cagr + dx, r.mix_part + dy, short, ha=ha, va="center", fontsize=10.5, color=INK2, fontweight="bold",
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=1), zorder=4)
    ax.set_xlim(-1.3, 3.4)
    ax.set_ylim(0, 1.0)
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.set_xlabel("From pay within education groups (percent a year)", fontsize=11, color=INK2, labelpad=8)
    ax.set_ylabel("From the change in education mix\n(percentage points a year)", fontsize=11, color=INK2, labelpad=8)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+.0f}%".replace("-", "\u2212") if v else "0%"))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+.1f}" if v else "0"))
    ax.spines["left"].set_visible(False)
    footer(fig, f"Source: U.S. Census Bureau, American Community Survey 1-year, tables B20004 and B15003. {len(d)} of {n_all} "
           f"metro and micro areas with comparable {first} and {last} boundaries; shown only where both parts pass a test at "
           f"90% confidence (the test for the education mix part is approximate). {first} dollars moved to {last} dollars "
           f"with the BLS R-CPI-U-RS. The two parts add up to the yearly change in the pay index.", h)
    fig.savefig(IMG / "04-pay-mix-metros.png", facecolor="white")
    plt.close(fig)


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    html = (ROOT / "dist" / "index.html").read_text()
    data = json.loads(re.search(r"const DATA = (\{.*?\});\n", html).group(1))
    geo = json.loads(re.search(r"const GEO = (\{.*?\});\n", html).group(1))
    first, last = str(data["first"]), str(data["last"])
    OUT.extend(["# Post chart tables (generated by scripts/post_charts.py)", ""])
    edu_chart(data, geo, first, last)
    coffee_chart()
    hero_chart(*pay_chart(data, first, last), first, last)
    pay_metro_chart(first, last)
    (ROOT / "data" / "clean" / "post_chart_tables.md").write_text("\n".join(OUT) + "\n")
    print("\n".join(OUT))


if __name__ == "__main__":
    main()
