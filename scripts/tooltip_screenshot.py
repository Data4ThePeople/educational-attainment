"""Screenshot of the map's pay tooltip for the New York metro area, for the
post. Copies dist/index.html to a temp folder with a small script that opens
the tooltip, renders it with headless Chrome, and crops the tooltip and New
York from the page. Run after build_viz.py.

Writes posts/educational-attainment/images/05-map-tooltip-new-york.png.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from mapping import ROOT  # noqa: E402

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
NEW_YORK = "310XX00US35620"
HASH = "topic=pay&level=cbsa&measure=paymix&view=change"
CROP = (560, 1090, 1450, 1960)  # at 2x scale in a 780 x 1500 window
OPEN_TIP = """<script>
window.addEventListener("load", () => setTimeout(() => {
  document.documentElement.setAttribute("data-theme", "light");
  const i = current.findIndex(f => f.id === "%s");
  const p = document.querySelector('path.a[data-k="' + i + '"]'), r = p.getBoundingClientRect();
  p.dispatchEvent(new PointerEvent("pointermove", {bubbles: true, clientX: r.left + r.width * 0.35, clientY: r.top + r.height * 0.45}));
}, 300));
</script></body>""" % NEW_YORK


def main():
    html = (ROOT / "dist" / "index.html").read_text()
    assert html.count("</body>") == 1
    with tempfile.TemporaryDirectory() as tmp:
        page, shot = Path(tmp) / "map.html", Path(tmp) / "full.png"
        page.write_text(html.replace("</body>", OPEN_TIP))
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=780,1500",
                        "--force-device-scale-factor=2", "--virtual-time-budget=5000", f"--screenshot={shot}",
                        f"file://{page}#{HASH}"], check=True, capture_output=True)
        out = ROOT / "posts" / "educational-attainment" / "images" / "05-map-tooltip-new-york.png"
        Image.open(shot).crop(CROP).save(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
