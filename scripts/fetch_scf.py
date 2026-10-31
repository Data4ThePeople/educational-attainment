"""Download the Survey of Consumer Finances (SCF) files used for the student
debt charts: full public data and replicate weights (Stata) for 2016 and
2025, plus the codebooks and the SAS macros that define the summary
variables. Files go to data/raw/scf/ and are unzipped to data/raw/scf/x/.
The zip files and x/ are not committed (see .gitignore); rerun this script.
"""
import sys
import zipfile
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from mapping import RAW  # noqa: E402

BASE = "https://www.federalreserve.gov/econres/files/"
YEARS = (2016, 2025)
DOCS = ["codebk2016.txt", "codebk2025.txt", "bulletin.macro.txt", "2025_scf_changes.pdf",
        "Standard_Error_Documentation.pdf"]


def main():
    out = RAW / "scf"
    out.mkdir(parents=True, exist_ok=True)
    zips = [f"scf{y}s.zip" for y in YEARS] + [f"scf{y}rw1s.zip" for y in YEARS]
    for name in zips + DOCS:
        path = out / name
        if not path.exists():
            r = requests.get(BASE + name, timeout=300)
            r.raise_for_status()
            path.write_bytes(r.content)
        print(f"{name}: {path.stat().st_size / 1e6:.1f} MB")
    for name in zips:
        with zipfile.ZipFile(out / name) as z:
            z.extractall(out / "x" / name[:-4])


if __name__ == "__main__":
    main()
