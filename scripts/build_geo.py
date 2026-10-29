"""Project the 2023 Census cartographic boundary files into SVG paths.

Input: data/raw/boundaries/{state,county,cbsa}/cb_2023_us_*_20m.shp, from
https://www2.census.gov/geo/tiger/GENZ2023/shp/ (1:20,000,000 scale). The 2023
files match what the 2025 ACS uses: Connecticut planning regions as counties,
and the July 2023 OMB metro and micro definitions.

Output: data/clean/geo_paths.json, {level: [{id, n, d}]}, with ids that match
panel.csv (states 0400000USss, counties 0500000USsssss, metro areas
310XX00UScbsa). Albers equal-area projection for the lower 48, with Alaska,
Hawaii and Puerto Rico moved into insets, all drawn in a 975 x 610 box.
"""
import json
import math
from pathlib import Path

import shapefile
from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parent.parent
BND = ROOT / "data" / "raw" / "boundaries"
OUT = ROOT / "data" / "clean" / "geo_paths.json"
W, H = 975, 610
TOL = 0.3          # simplification tolerance, in output pixels
MIN_AREA = 0.6     # drop polygon parts smaller than this many square pixels

# Albers parameters per region: (standard parallel 1, 2, origin lat, central lon)
ALBERS = {
    "l48": (29.5, 45.5, 37.5, -96.0),
    "ak": (55.0, 65.0, 50.0, -154.0),
    "hi": (8.0, 18.0, 13.0, -157.0),
    "pr": (8.0, 18.0, 13.0, -66.0),
}
# Box each region is fitted into: (x0, y0, x1, y1)
BOX = {
    "l48": (10, 10, 965, 600),
    "ak": (10, 440, 215, 600),
    "hi": (225, 520, 345, 600),
    "pr": (880, 555, 960, 600),
}
STATE_REGION = {"02": "ak", "15": "hi", "72": "pr"}


def albers(p1, p2, lat0, lon0):
    r = math.radians
    n = (math.sin(r(p1)) + math.sin(r(p2))) / 2
    c = math.cos(r(p1)) ** 2 + 2 * n * math.sin(r(p1))
    rho0 = math.sqrt(c - 2 * n * math.sin(r(lat0))) / n

    def f(lon, lat):
        if lon0 < -140 and lon > 0:      # Aleutians cross the 180th meridian
            lon -= 360
        rho = math.sqrt(c - 2 * n * math.sin(r(lat))) / n
        th = n * r(lon - lon0)
        return rho * math.sin(th), -(rho0 - rho * math.cos(th))   # y down
    return f


def region_of(level, rec, geom):
    if level in ("state", "county"):
        return STATE_REGION.get(rec["STATEFP"], "l48")
    lon, lat = geom.centroid.x, geom.centroid.y
    if lat > 50 or lon < -165 or lon > 170:
        return "ak"
    if lat < 23 and lon < -150:
        return "hi"
    if lat < 19.5 and lon > -68:
        return "pr"
    return "l48"


def load(level):
    r = shapefile.Reader(str(BND / level / f"cb_2023_us_{level}_20m.shp"))
    out = []
    for sr in r.iterShapeRecords():
        rec = sr.record.as_dict()
        geom = shape(sr.shape.__geo_interface__)
        out.append((rec, geom, region_of(level, rec, geom)))
    return out


def projector(states):
    """For each region, a function lon/lat -> output pixels, fitted to its box
    using the state shapes of that region."""
    fits = {}
    for reg, params in ALBERS.items():
        proj = albers(*params)
        geoms = [transform(lambda xs, ys, zs=None: _proj_xy(proj, xs, ys), g)
                 for rec, g, rg in states if rg == reg]
        minx = min(g.bounds[0] for g in geoms); miny = min(g.bounds[1] for g in geoms)
        maxx = max(g.bounds[2] for g in geoms); maxy = max(g.bounds[3] for g in geoms)
        x0, y0, x1, y1 = BOX[reg]
        k = min((x1 - x0) / (maxx - minx), (y1 - y0) / (maxy - miny))
        ox = x0 + ((x1 - x0) - k * (maxx - minx)) / 2 - k * minx
        oy = y0 + ((y1 - y0) - k * (maxy - miny)) / 2 - k * miny
        fits[reg] = (proj, k, ox, oy)
    return fits


def _proj_xy(proj, xs, ys):
    pts = [proj(a, b) for a, b in zip(xs, ys)]
    return [p[0] for p in pts], [p[1] for p in pts]


def to_pixels(geom, fit):
    proj, k, ox, oy = fit

    def f(xs, ys, zs=None):
        px, py = _proj_xy(proj, xs, ys)
        return [ox + k * a for a in px], [oy + k * b for b in py]
    return transform(f, geom)


def path_d(geom):
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    parts = []
    for poly in polys:
        if poly.is_empty or poly.area < MIN_AREA:
            continue
        for ring in [poly.exterior, *poly.interiors]:
            c = list(ring.coords)[:-1]
            if len(c) < 3:
                continue
            parts.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in c) + "Z")
    return "".join(parts)


def main():
    states = load("state")
    fits = projector(states)
    out = {"w": W, "h": H}
    for level in ("state", "county", "cbsa"):
        feats = []
        for rec, geom, reg in (states if level == "state" else load(level)):
            g = to_pixels(geom, fits[reg]).simplify(TOL, preserve_topology=True)
            d = path_d(g)
            if not d:
                continue
            if level == "cbsa":
                gid, name = "310XX00US" + rec["GEOID"], rec["NAMELSAD"]
            elif level == "county":
                gid, name = rec["GEOIDFQ"], f"{rec['NAMELSAD']}, {rec['STATE_NAME']}"
            else:
                gid, name = rec["GEOIDFQ"], rec["NAME"]
            feats.append({"id": gid, "n": name, "d": d})
        ids = [f["id"] for f in feats]
        assert len(ids) == len(set(ids)), f"duplicate ids in {level}"
        out[level] = feats
        print(level, len(feats), "shapes,", sum(len(f["d"]) for f in feats) // 1000, "KB of path data")
    OUT.write_text(json.dumps(out, separators=(",", ":")))


if __name__ == "__main__":
    main()
