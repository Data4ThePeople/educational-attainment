"""Pull ACS 1-year tables from the Census API and save each response as-is.

Saves to data/raw/<year>/:
  variables_<table>.json   the table's variable labels for that year
  geography.json           the geography levels the API offers that year
  <table>_<level>.json     the API response, unchanged

The API key is loaded with d4tp_env and never written to disk or printed.
Re-running skips files that already exist; pass --force to pull again.
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, os.path.expanduser("~/.claude/d4tp-process"))
from d4tp_env import load_env, get_key  # noqa: E402

load_env()
KEY = get_key("CENSUS_API_KEY")

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
BASE = "https://api.census.gov/data/{year}/acs/acs1"

# No standard 2020 1-year release; left as a gap.
YEARS = [y for y in range(2008, 2026) if y != 2020]
TIEOUT_YEARS = [2019, 2023, 2025]

CBSA = "metropolitan statistical area/micropolitan statistical area"
LEVELS = {
    "us": {"for": "us:1"},
    "region": {"for": "region:*"},
    "division": {"for": "division:*"},
    "state": {"for": "state:*"},
    "county": {"for": "county:*", "in": "state:*"},
    "cbsa": {"for": f"{CBSA}:*"},
    "place": {"for": "place:*", "in": "state:*"},
}
DETAIL_TABLES = ["B15003", "B15002", "B99151"]


def scrub(text):
    return str(text).replace(KEY, "<key>")


def get(url, params, tries=4):
    params = dict(params, key=KEY)
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=120)
        except requests.RequestException as e:
            err = scrub(e)
        else:
            if r.status_code == 200:
                return r
            if r.status_code in (204, 404):
                return r
            err = f"HTTP {r.status_code}: {scrub(r.text[:300])}"
        time.sleep(3 * (i + 1))
    raise RuntimeError(f"{url} {scrub(params.get('for'))}: {err}")


def save(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def pull_meta(year, force):
    ydir = RAW / str(year)
    base = BASE.format(year=year)
    for table, sub in [(t, "") for t in DETAIL_TABLES] + [("S1501", "/subject")]:
        out = ydir / f"variables_{table}.json"
        if out.exists() and not force:
            continue
        r = get(f"{base}{sub}/groups/{table}.json", {})
        if r.status_code == 200:
            save(out, r.text)
    out = ydir / "geography.json"
    if force or not out.exists():
        save(out, get(f"{base}/geography.json", {}).text)


def pull_level(year, table, level, spec, sub="", force=False):
    out = RAW / str(year) / f"{table}_{level}.json"
    if out.exists() and not force:
        return "cached"
    url = BASE.format(year=year) + sub
    params = {"get": f"NAME,group({table})", **spec}
    r = get(url, params)
    if r.status_code == 200 and r.text.strip():
        save(out, r.text)
        return f"{len(r.json()) - 1} rows"
    # Some older years reject the state wildcard for places and counties;
    # fall back to one call per state and save the combined response.
    if "in" in spec:
        states = json.loads((RAW / str(year) / f"{table}_state.json").read_text())
        si = states[0].index("state")
        header, rows = None, []
        for s in states[1:]:
            rr = get(url, {**params, "in": f"state:{s[si]}"})
            if rr.status_code != 200 or not rr.text.strip():
                continue
            js = rr.json()
            header = header or js[0]
            rows.extend(js[1:])
        if header:
            save(out, json.dumps([header] + rows))
            return f"{len(rows)} rows (per state)"
    return f"none (HTTP {r.status_code})"


def main():
    force = "--force" in sys.argv
    for year in YEARS:
        pull_meta(year, force)
        for table in DETAIL_TABLES:
            for level, spec in LEVELS.items():
                print(year, table, level, pull_level(year, table, level, spec, force=force), flush=True)
        if year in TIEOUT_YEARS:
            for level in ("us", "state"):
                print(year, "S1501", level,
                      pull_level(year, "S1501", level, LEVELS[level], "/subject", force), flush=True)


if __name__ == "__main__":
    main()
