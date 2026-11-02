"""Static map for the email teaser (EMAIL.md): the map page's change in the share of adults 25
and over with a bachelor's degree or more, 2015 to 2025, by metro and micro
area. Copies dist/index.html to a temp folder with a small script that sets
the light theme and hides the controls, intro text and collapsed sections,
then renders the card with headless Chrome. Run after build_viz.py.

Writes posts/educational-attainment/images/01-ba-change-map.png.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from mapping import ROOT  # noqa: E402

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HASH = "topic=edu&level=cbsa&measure=baplus&view=change"
OUT = ROOT / "posts" / "educational-attainment" / "images" / "01-ba-change-map.png"
WIDTH, SCALE = 780, 2
PREP = """<style>#h1, .sub, .controls, #intro, details { display: none !important; }</style>
<script>
document.documentElement.setAttribute("data-theme", "light");
window.addEventListener("load", () => setTimeout(() => {
  const r = document.querySelector(".card").getBoundingClientRect();
  const d = document.createElement("pre"); d.id = "rect"; d.style.display = "none";
  d.textContent = `RECT ${r.left} ${r.top} ${r.right} ${r.bottom} INTRO ${document.getElementById("intro").textContent}`;
  document.body.appendChild(d);
}, 300));
</script></body>"""


def chrome(*args):
    return subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=5000",
                           *args], check=True, capture_output=True, text=True).stdout


def render(hash_, out, scale=SCALE, step=None):
    """Render the map page's card for one view (a URL hash) to out. step fixes the size of the legend's color
    steps instead of the page's own choice. Returns the view's intro text."""
    html = (ROOT / "dist" / "index.html").read_text()
    assert html.count("</body>") == 1 and html.count("<head>") == 1
    if step:
        html = html.replace("<head>", f"<head><script>window.STEP_OVERRIDE = {step};</script>")
    with tempfile.TemporaryDirectory() as tmp:
        page, shot = Path(tmp) / "map.html", Path(tmp) / "full.png"
        page.write_text(html.replace("</body>", PREP))
        url = f"file://{page}#{hash_}"
        dom = chrome(f"--window-size={WIDTH},1600", "--dump-dom", url)
        m = re.search(r"RECT ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) INTRO ([^<]*)", dom)
        left, top, right, bottom = (float(v) for v in m.groups()[:4])
        chrome(f"--window-size={WIDTH},{int(bottom) + 40}", f"--force-device-scale-factor={scale}", f"--screenshot={shot}", url)
        box = tuple(round(v * scale) for v in (left, top, right, bottom))
        Image.open(shot).crop(box).save(out)
    return m.group(5)


def main():
    render(HASH, OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
