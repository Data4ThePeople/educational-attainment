"""Social animation: the map page's three pay index views for metro and micro
areas, 2015 to 2025, shown in turn: total growth, growth from the change in
pay within education groups, and growth from the change in education mix.
Each frame is the map page itself (scripts/map_screenshot.py), so the last
frame matches the map's education mix view, except that all three frames share one
color scale (STEP) so their colors compare. Run after build_viz.py.

Writes posts/educational-attainment/social/pay-index-maps.gif.
"""
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from mapping import ROOT  # noqa: E402
from map_screenshot import render  # noqa: E402

VIEWS = [("paytotal", 3500), ("payfixed", 3500), ("paymix", 5000)]  # frame, milliseconds shown
WIDTH = 720
STEP = 0.5  # one color scale for all three views: steps at 0.5 and 1.0 (percent or points a year)


def main():
    out = ROOT / "posts" / "educational-attainment" / "social" / "pay-index-maps.gif"
    out.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        shots = []
        for key, _ in VIEWS:
            path = Path(tmp) / f"{key}.png"
            render(f"topic=pay&level=cbsa&measure={key}&view=change", path, step=STEP)
            shots.append(Image.open(path).convert("RGB"))
    # The legends differ in height, so every frame goes on one canvas, top-aligned, filled with the card color.
    w, h = max(s.width for s in shots), max(s.height for s in shots)
    sized = []
    for s in shots:
        canvas = Image.new("RGB", (w, h), s.getpixel((s.width // 2, s.height - 4)))
        canvas.paste(s, (0, 0))
        sized.append(canvas.resize((WIDTH, round(h * WIDTH / w)), Image.LANCZOS))
    # One palette from all three frames, so a color means the same thing in every frame.
    strip = Image.new("RGB", (WIDTH, sized[0].height * len(sized)))
    for i, f in enumerate(sized):
        strip.paste(f, (0, i * f.height))
    palette = strip.quantize(colors=192, dither=Image.NONE)
    frames = [f.quantize(palette=palette, dither=Image.NONE) for f in sized]
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=[d for _, d in VIEWS], loop=0, optimize=True)
    print("wrote", out, frames[0].size, f"{out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
