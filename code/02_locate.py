"""Read the 40 sheets, extract the drawn coastline, place each sheet on the modern map, and make the web images.

1. Coastline extraction (quarter resolution, 960 px wide). The sheets are watercolour on paper: land is shown by green
   hachures, the surveyed coast by a dark ink line (often with a red survey line), the sea is blank paper. A pixel is
   coast if it is dark or red ink, lies within 6 quarter-px of green hachure, and belongs to an ink stroke at least 40
   quarter-px long (this drops most labels). Land and sea masks near the coast are kept for the search in step 2.
2. Where is each sheet? (argument `search`, slow, about two hours on two cores.) For every sheet, a brute-force search over
   position, rotation (-15 to 15 degrees) and scale (around the nominal 1:43,600, see below) for the placement whose land
   and sea best agree with Natural Earth's land, by FFT correlation on a 1 km grid of Japan and the Kurils. The best
   placements were then checked by eye on overlays of the modern coast drawn on each sheet, and the result is the hand-
   checked table data/sheet_index.csv (status, region and a starting position and rotation of the centre of every sheet). Without it the
   table is read as it is.
3. Rigid coastline fit. From the starting position, an iterative closest point fit (rotation and translation, trimmed to
   the closest 70% of coast pixels) of the drawn coast to Natural Earth's 1:10m coast, with the scale fixed at the
   nominal one. Output: data/sheets.json (fit and extracted coast for every located sheet).
   Nominal scale. LoC's catalogue gives 1:43,600 for Hokkaido. At that scale, Ino's 'ri' of 36 cho is 9.0 cm. Sheet 5
   (Notsuke) has a shape that fixes its scale; it gives 6.66 m of ground per pixel of the full-size LoC scan, which
   implies a scan resolution of about 166 dpi. All other sheets are assumed to share it (each scan's pixel size is
   known from its original width in raw/commons_meta.json); step 03 then tests that assumption sheet by sheet.
4. Web images: img/sheet_N.jpg (1,600 px on the long side) for every sheet, img/whole1878.jpg and img/replica.jpg."""
import sys, numpy as np, pandas as pd
from PIL import Image
from scipy import ndimage as nd
from scipy.spatial import cKDTree
from common import *

Image.MAX_IMAGE_PIXELS = None
META = jload(f"{RAW}/commons_meta.json")
ORIG = {int(m["t"].split("-")[-1][:-4]): (m["w"], m["h"]) for m in META if "LOC 2001620020" in m["t"]}
M_PER_ORIG_PX = 6.66                    # calibrated on sheet 5, see above
SEARCH = "search" in sys.argv[1:]


def masks(i, f=QPX):
    im = Image.open(f"{RAW}/sheets/sheet_2001620020-{i}.jpg").convert("RGB")
    W, H = im.size
    im = im.resize((W // f, H // f), Image.BILINEAR)
    a = np.asarray(im).astype(float); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    gr = g - r; gbase = nd.median_filter(gr, size=41)
    green = ((gr - gbase) > 8) & ((g - b) > 15)
    dark = a.sum(-1) < nd.median_filter(a.sum(-1), size=41) - 120
    red = ((r - g) > 45) & (r > 120)
    return (W, H), green, dark | red


def coast_of(i):
    cf = f"{WORK}/coast_{i}.npz"
    if os.path.exists(cf):
        z = np.load(cf); return tuple(z["size"]), z["coast"], z["land"], z["sea"]
    size, green, ink = masks(i)
    lab, n = nd.label(nd.binary_dilation(ink, iterations=1)); sl = nd.find_objects(lab)
    keep = np.zeros(n + 1, bool)
    for k, s in enumerate(sl):
        if max(s[0].stop - s[0].start, s[1].stop - s[1].start) >= 40:
            keep[k + 1] = True
    coast = keep[lab] & ink & nd.binary_dilation(green, iterations=6)
    L = nd.binary_fill_holes(nd.binary_closing(green, iterations=8) | nd.binary_dilation(green, iterations=3))
    for m in (coast, L):
        m[:15, :] = 0; m[-15:, :] = 0; m[:, :15] = 0; m[:, -15:] = 0
    near = nd.distance_transform_edt(~coast) < 30
    sea = near & ~nd.binary_dilation(L, iterations=4) & ~coast
    land = L & near
    np.savez_compressed(cf, size=size, coast=coast, land=land, sea=sea)
    return size, coast, land, sea


TF, TI = proj()
CO = np.load(f"{WORK}/coast_lcc.npy"); TREE = cKDTree(CO)


def apply(A, x, y):
    return A[0, 0] * x + A[0, 1] * y + A[0, 2], A[1, 0] * x + A[1, 1] * y + A[1, 2]


def icp_rigid(xs, ys, A, s, iters=40, trim=0.7, maxd=8000):
    """xs, ys in full-size sheet px (3,840 frame). Rotation and translation; s = metres per px (fixed)."""
    P0 = np.c_[xs * s, -ys * s]
    for _ in range(iters):
        X, Y = apply(A, xs, ys); d, j = TREE.query(np.c_[X, Y])
        m = d <= min(np.quantile(d, trim), maxd)
        P, Q = P0[m], CO[j[m]]; pc, qc = P.mean(0), Q.mean(0)
        U, _, Vt = np.linalg.svd((P - pc).T @ (Q - qc)); R = Vt.T @ U.T
        if np.linalg.det(R) < 0:
            Vt[-1] *= -1; R = Vt.T @ U.T
        t = qc - R @ pc
        A = np.array([[R[0, 0] * s, -R[0, 1] * s, t[0]], [R[1, 0] * s, -R[1, 1] * s, t[1]]])
    X, Y = apply(A, xs, ys); d, _ = TREE.query(np.c_[X, Y])
    return A, d


def thin(xs, ys, cell=8):
    """one coast point per 8 x 8 px cell of the 3,840 px image (about 80 m on the ground)"""
    k = np.unique(np.c_[(xs // cell).astype(int), (ys // cell).astype(int)], axis=0)
    return (k * cell + cell // 2).astype(int).tolist()


def search(i, s_full):
    """Brute-force placement search (see docstring). Returns the best (score, lat, lon, rotation)."""
    from scipy.signal import fftconvolve
    from PIL import ImageDraw
    cell = 1000.0; X0, Y0, X1, Y1 = -1000e3, -1050e3, 1000e3, 1000e3
    Wd, Hd = int((X1 - X0) / cell), int((Y1 - Y0) / cell)
    im = Image.new("L", (Wd, Hd), 0); dr = ImageDraw.Draw(im)
    from shapely.geometry import shape
    for f in jload(f"{DATA}/japan.json")["features"]:
        g = shape(f["geometry"])
        for p in getattr(g, "geoms", [g]):
            xy = np.array(p.exterior.coords); X, Y = TF.transform(xy[:, 0], xy[:, 1])
            dr.polygon([((x - X0) / cell, (Y1 - y) / cell) for x, y in zip(X, Y)], fill=255)
    M = np.where(np.asarray(im) > 0, 1.0, -1.0).astype(np.float32)
    _, coast, land, sea = coast_of(i)
    ly, lx = np.nonzero(land); sy, sx = np.nonzero(sea)
    cx, cy = np.r_[lx, sx].mean(), np.r_[ly, sy].mean(); best = None
    for sc in (0.94, 1, 1.06):
        s = s_full * QPX * sc
        for rot in range(-15, 16, 3):
            t = np.radians(rot)
            def tr(xs, ys):
                u = (xs - cx) * s; v = -(ys - cy) * s
                return (u * np.cos(t) - v * np.sin(t)) / cell, (u * np.sin(t) + v * np.cos(t)) / cell
            LX, LY = tr(lx, ly); SX, SY = tr(sx, sy)
            mnx = min(LX.min(), SX.min()); mxy = max(LY.max(), SY.max())
            K = np.zeros((int(mxy - min(LY.min(), SY.min())) + 2, int(max(LX.max(), SX.max()) - mnx) + 2), np.float32)
            np.add.at(K, (np.round(mxy - LY).astype(int), np.round(LX - mnx).astype(int)), 1.0 / len(lx))
            np.add.at(K, (np.round(mxy - SY).astype(int), np.round(SX - mnx).astype(int)), -1.0 / len(sx))
            R = fftconvolve(M, K[::-1, ::-1], mode="valid") / 2
            j = np.unravel_index(np.argmax(R), R.shape)
            ex = X0 + (j[1] - mnx) * cell; ny = Y1 - (j[0] + mxy) * cell
            if best is None or R[j] > best[0]:
                lon, lat = TI.transform(ex, ny); best = (float(R[j]), lat, lon, rot)
    return best


IDX = pd.read_csv(f"{DATA}/sheet_index.csv")
out = {}
for r in IDX.itertuples():
    i = int(r.sheet)
    size, coast, land, sea = coast_of(i)
    s_full = M_PER_ORIG_PX * ORIG[i][0] / size[0]               # metres per px of the 3,840 px image, nominal scale
    rec = {"sheet": i, "w": int(size[0]), "h": int(size[1]), "orig_w": ORIG[i][0], "orig_h": ORIG[i][1], "status": r.status}
    if SEARCH:
        rec["search"] = search(i, s_full); print(i, "search", rec["search"], flush=True)
    yy, xx = np.nonzero(coast)
    xs = xx * QPX + QPX / 2; ys = yy * QPX + QPX / 2                # full-size px
    rec["coast_px"] = thin(xs, ys)
    xs, ys = np.array(rec["coast_px"], float).T if rec["coast_px"] else (xs, ys)
    if r.status == "located":
        ex, ny = TF.transform(r.init_lon, r.init_lat); t = np.radians(r.init_rot)
        cx, cy = size[0] / 2, size[1] / 2; c, sn = np.cos(t), np.sin(t)       # starting position is that of the sheet's centre
        A = np.array([[s_full * c, s_full * sn, 0], [s_full * sn, -s_full * c, 0]])
        A[0, 2] = ex - (A[0, 0] * cx + A[0, 1] * cy); A[1, 2] = ny - (A[1, 0] * cx + A[1, 1] * cy)
        A, d = icp_rigid(xs, ys, A, s_full)
        A, d = icp_rigid(xs, ys, A, s_full, trim=0.8)
        rec.update({"rigid": A.tolist(), "m_per_px_nominal": s_full, "rigid_median_m": float(np.median(d))})
        lon, lat = TI.transform(*apply(A, np.array([xs.mean()]), np.array([ys.mean()])))
        print(i, r.place, "median coast distance", round(float(np.median(d))), "m at", round(lat[0], 3), round(lon[0], 3), flush=True)
    out[i] = rec
jsave(out, f"{DATA}/sheets.json")

# web images
for i in range(1, 41):
    im = Image.open(f"{RAW}/sheets/sheet_2001620020-{i}.jpg").convert("RGB")
    k = 1600 / max(im.size)
    im.resize((round(im.size[0] * k), round(im.size[1] * k)), Image.LANCZOS).save(f"{IMG}/sheet_{i}.jpg", quality=72, optimize=True, progressive=True)
im = Image.open(f"{RAW}/japan_ino_1878_whole.jpg").convert("RGB"); im.save(f"{IMG}/whole1878.jpg", quality=80, optimize=True, progressive=True)
im = Image.open(f"{RAW}/inoh_taizu_replica_all_sheets.jpg").convert("RGB"); im.save(f"{IMG}/replica.jpg", quality=80, optimize=True)
print("images", sum(os.path.getsize(f"{IMG}/{f}") for f in os.listdir(IMG)) // 1024, "KB")
