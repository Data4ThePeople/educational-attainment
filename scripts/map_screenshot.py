"""Static map for the post: the map page's change in the share of adults 25
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
WIDTH, SCALE = 780, 2
PREP = """<style>#h1, .sub, .controls, #intro, details { display: none !important; }</style>
<script>
document.documentElement.setAttribute("data-theme", "light");
window.addEventListener("load", () => setTimeout(() => {
  const r = document.querySelector(".card").getBoundingClientRect();
  const d = document.createElement("pre"); d.id = "rect"; d.style.display = "none";
  d.textContent = `RECT ${r.left} ${r.top} ${r.right} ${r.bottom}`;
  document.body.appendChild(d);
}, 300));
</script></body>"""


def chrome(*args):
    return subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=5000",
                           *args], check=True, capture_output=True, text=True).stdout


def main():
    html = (ROOT / "dist" / "index.html").read_text()
    assert html.count("</body>") == 1
    with tempfile.TemporaryDirectory() as tmp:
        page, shot = Path(tmp) / "map.html", Path(tmp) / "full.png"
        page.write_text(html.replace("</body>", PREP))
        url = f"file://{page}#{HASH}"
        dom = chrome(f"--window-size={WIDTH},1600", "--dump-dom", url)
        left, top, right, bottom = (float(v) for v in re.search(r"RECT ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+)", dom).groups())
        chrome(f"--window-size={WIDTH},{int(bottom) + 40}", f"--force-device-scale-factor={SCALE}", f"--screenshot={shot}", url)
        out = ROOT / "posts" / "educational-attainment" / "images" / "01-ba-change-map.png"
        box = tuple(round(v * SCALE) for v in (left, top, right, bottom))
        Image.open(shot).crop(box).save(out)
    print("wrote", out, box)


if __name__ == "__main__":
    main()
