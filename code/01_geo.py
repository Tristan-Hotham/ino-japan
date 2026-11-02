"""Modern outlines: data/japan.json (Natural Earth 1:10m land of Japan and of the islands now administered by Russia,
clipped to the area Ino's maps cover, lon/lat to 5 decimals) and data/world.json (Natural Earth 1:50m countries of
East Asia, simplified, for overview maps). Also the coast as dense points for the fits (WORK/coast_lcc.npy)."""
import numpy as np
from shapely.geometry import shape, mapping, box
from common import *

BB = box(127, 29, 149.6, 47.6)


def rnd(c, k):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


W10 = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
feats = []
for f in W10["features"]:
    a3 = f["properties"]["ADM0_A3"]
    if a3 not in ("JPN", "RUS"):
        continue
    g = shape(f["geometry"]).intersection(BB)
    if g.is_empty:
        continue
    feats.append({"type": "Feature", "properties": {"iso": a3}, "geometry": {"type": g.geom_type, "coordinates": rnd(mapping(g)["coordinates"], 5)}})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/japan.json")

W50 = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
wf = []
for f in W50["features"]:
    g = shape(f["geometry"]).intersection(box(110, 18, 160, 56))
    if g.is_empty:
        continue
    g = g.simplify(0.03, preserve_topology=True)
    wf.append({"type": "Feature", "properties": {"iso": f["properties"]["ADM0_A3"]}, "geometry": {"type": g.geom_type, "coordinates": rnd(mapping(g)["coordinates"], 3)}})
jsave({"type": "FeatureCollection", "features": wf}, f"{DATA}/world.json")

# dense coast points in the projection, for the coastline fits (a point every 100 m along every ring)
TF, TI = proj()
P = []
for f in feats:
    g = shape(f["geometry"])
    for p in getattr(g, "geoms", [g]):
        xy = np.array(p.exterior.coords)
        X, Y = TF.transform(xy[:, 0], xy[:, 1]); L = np.c_[X, Y]
        for a, b in zip(L[:-1], L[1:]):
            d = np.hypot(*(b - a))
            if d > 15000:          # long straight edges along the clipping box are not coast
                la, lb = TI.transform(*a), TI.transform(*b)
                onb = lambda q: abs(q[0] - 127) < 1e-3 or abs(q[0] - 149.6) < 1e-3 or abs(q[1] - 29) < 1e-3 or abs(q[1] - 47.6) < 1e-3
                if onb(la) and onb(lb):
                    continue
            n = max(1, int(d / 100)); t = np.linspace(0, 1, n, endpoint=False)[:, None]; P.append(a + t * (b - a))
np.save(f"{WORK}/coast_lcc.npy", np.vstack(P))
print("japan.json", len(feats), "features;", os.path.getsize(f"{DATA}/japan.json") // 1024, "KB; world.json", os.path.getsize(f"{DATA}/world.json") // 1024, "KB; coast points", sum(len(p) for p in P))
