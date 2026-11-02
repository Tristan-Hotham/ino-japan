"""How close did he get? Fits of every located sheet to the modern coast, tie points, control points and the
national check. Reads data/sheets.json, data/sheet_index.csv, data/control_points.csv, data/national_points.csv and the
Natural Earth coast (WORK/coast_lcc.npy from 01_geo.py). Writes data/fits.json, data/tie_points.csv,
data/control_points_fit.csv and data/national_fit.csv.

All positions are on the Lambert conformal conic projection in common.LCC (metres); directions are corrected for the
projection's meridian convergence, so 'rotation' is relative to true north.

  * Coastline fits. The drawn coast of each sheet (sheet pixels) is fitted to Natural Earth's 1:10m coast by trimmed
    iterative closest point: rigid with the nominal scale (step 02), then affine (6 parameters), then quadratic
    (12 parameters, the higher-order check). The agreement is the distance from each drawn coast point to the nearest
    modern coast after the fit.
  * Tie points. Every 3 km along the drawn coast, a window of radius 2.5 km of drawn coast is matched to the modern coast
    by a local translation (iterative closest point, after the sheet's affine fit). A window counts only if its matched
    modern coast turns enough to fix the shift in both directions (the smaller eigenvalue of the summed outer product
    of coast normals is at least 0.15 of the larger) and its matched coast lies within 600 m on median. A straight
    beach fixes position only across the shore, so it gives no tie point.
  * Point fits. An affine fit of sheet pixels to modern positions over each sheet's tie points (6 or more), with
    leave-one-out errors; a quadratic fit where there are 12 or more. Errors are horizontal distances in metres.
  * Control points. The capes, spit tips and bends I picked by eye (data/control_points.csv) are not used in any fit;
    their residuals against the sheet's coastline affine fit are an independent check.
  * National check. 18 capes and island centres picked by eye on the 1878 whole-Japan map, compared with their
    modern positions by a similarity fit (rotation, one scale, shift) and an affine fit (separate east-west and
    north-south scales); errors are split into north-south (latitude) and east-west (longitude) parts."""
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from common import *

TF, TI = proj()
CO = np.load(f"{WORK}/coast_lcc.npy"); TREE = cKDTree(CO)
S = jload(f"{DATA}/sheets.json")
IDX = pd.read_csv(f"{DATA}/sheet_index.csv").set_index("sheet")
GCP = pd.read_csv(f"{DATA}/control_points.csv")
TIE_COND = 0.10                        # coast windows must turn enough to fix a shift in both directions
DRAW_MM = 0.5                          # a careful draughtsman's line and placing error on paper, mm
SCALE = SCALE_HOKKAIDO


def design(x, y, order):
    if order == 1: return np.c_[x, y, np.ones_like(x)]
    return np.c_[x, y, np.ones_like(x), x * x, x * y, y * y]


def simfit(x, y, X, Y):
    """similarity (rotation, one scale, shift) with the image y axis pointing down; returned as affine coefficients"""
    M = np.zeros((2 * len(x), 4)); M[0::2, 0] = x; M[0::2, 1] = y; M[0::2, 2] = 1; M[1::2, 0] = -y; M[1::2, 1] = x; M[1::2, 3] = 1
    a, b, c, e = np.linalg.lstsq(M, np.c_[X, Y].reshape(-1), rcond=None)[0]
    return np.array([a, b, c]), np.array([b, -a, e])


def fit(x, y, X, Y, order=1):
    D = design(x, y, order); cx, *_ = np.linalg.lstsq(D, X, rcond=None); cy, *_ = np.linalg.lstsq(D, Y, rcond=None)
    return cx, cy


def ev(c, x, y, order):
    D = design(x, y, order); return D @ c[0], D @ c[1]


def icp(x, y, c, order, iters=30, trim=0.8):
    for _ in range(iters):
        X, Y = ev(c, x, y, order); d, j = TREE.query(np.c_[X, Y])
        m = d <= np.quantile(d, trim)
        c = fit(x[m], y[m], CO[j[m], 0], CO[j[m], 1], order)
    X, Y = ev(c, x, y, order); d, _ = TREE.query(np.c_[X, Y])
    return c, d


def north_angle(X, Y):
    """angle (deg, anticlockwise from grid +y) of true north at a projected point"""
    lon, lat = TI.transform(X, Y); X2, Y2 = TF.transform(lon, lat + 0.01)
    return np.degrees(np.arctan2(-(X2 - X), Y2 - Y))


def normals(P, r=400.0):
    out = np.zeros_like(P)
    for k, p in enumerate(P):
        nb = CO[TREE.query_ball_point(p, r)]
        if len(nb) < 3: continue
        w, v = np.linalg.eigh(np.cov((nb - nb.mean(0)).T)); t = v[:, 1]
        out[k] = [-t[1], t[0]]
    return out


def affine_props(c):
    """c: affine coefficients for (x, y_down) -> (E, N). Scale (m/px), anisotropy, grid rotation of 'up'."""
    M = np.array([[c[0][0], c[0][1]], [c[1][0], c[1][1]]]) @ np.diag([1, -1])     # y up
    U, s, Vt = np.linalg.svd(M)
    up = M @ np.array([0, 1.0])
    return float(np.sqrt(abs(np.linalg.det(M)))), float(s[0] / s[1]), float(np.degrees(np.arctan2(-up[0], up[1])))


fits, ties, gres = {}, [], []
for key, rec in S.items():
    i = int(key)
    if rec["status"] != "located":
        continue
    P = np.array(rec["coast_px"], float); x, y = P[:, 0], P[:, 1]
    A = np.array(rec["rigid"]); c0 = (A[0], A[1])
    X, Y = ev(c0, x, y, 1); d0, j0 = TREE.query(np.c_[X, Y])
    Xc, Yc = ev(c0, np.array([rec["w"] / 2]), np.array([rec["h"] / 2]), 1)
    lon_c, lat_c = TI.transform(Xc[0], Yc[0])
    north = float(north_angle(Xc[0], Yc[0]))
    scale, aniso, rotg = affine_props(c0)
    nm0 = normals(CO[np.unique(j0)][::3]); nm0 = nm0[np.hypot(nm0[:, 0], nm0[:, 1]) > 0]; e0 = np.linalg.eigvalsh(nm0.T @ nm0)
    # checkpoints every 1 km of drawn coast (their count is the length of drawn coast measured, in km)
    Pg = np.c_[X, Y]; cp = []
    for k in np.argsort(x):
        if all(np.hypot(*(Pg[k] - q)) >= 1000 for q in cp):
            cp.append(Pg[k])
    cp = np.array(cp); dcp, jcp = TREE.query(cp)
    # ---- tie windows: 4 km of drawn coast matched by a local shift where the coast turns enough ----
    centres = []
    for p in Pg:
        if all(np.hypot(*(p - q)) >= 3000 for q in centres):
            centres.append(p)
    tl = []
    for q in centres:
        w = np.hypot(Pg[:, 0] - q[0], Pg[:, 1] - q[1]) < 4000
        if w.sum() < 30: continue
        Q = Pg[w]; t = np.zeros(2)
        for _ in range(15):
            d, j = TREE.query(Q + t); m = d <= np.quantile(d, 0.8)
            t = t + (CO[j[m]] - (Q[m] + t)).mean(0)
        d, j = TREE.query(Q + t)
        if np.median(d) > 600 or np.hypot(*t) > 3000: continue
        nm = normals(CO[np.unique(j)]); nm = nm[np.hypot(nm[:, 0], nm[:, 1]) > 0]
        if len(nm) < 5: continue
        e = np.linalg.eigvalsh(nm.T @ nm)
        if e[0] / e[1] < TIE_COND: continue
        cx_, cy_ = x[w].mean(), y[w].mean()
        Em, Nm = ev(c0, np.array([cx_]), np.array([cy_]), 1)
        lon, lat = TI.transform(Em[0] + t[0], Nm[0] + t[1])
        tl.append(["tie", f"{i}-t{len(tl) + 1}", "coast window", "auto", "", round(cx_), round(cy_), round(lat, 5), round(lon, 5), round(float(np.median(d))), round(float(e[0] / e[1]), 2)])
    for g in GCP[GCP.sheet == i].itertuples():
        tl.append(["hand", g.gcp, g.kind, g.conf, g.note if isinstance(g.note, str) else "", g.x, g.y, g.lat, g.lon, None, None])
    T = pd.DataFrame(tl, columns=["source", "id", "kind", "conf", "note", "x", "y", "lat", "lon", "match_m", "conditioning"])
    T.insert(0, "sheet", i)
    T["E"], T["N"] = TF.transform(T.lon.values, T.lat.values) if len(T) else ([], [])
    # residuals against the coastline fit (rigid, nominal scale): from where the sheet puts the feature to where it is
    if len(T):
        Xr, Yr = ev(c0, T.x.values.astype(float), T.y.values.astype(float), 1)
        T["map_lon"], T["map_lat"] = TI.transform(Xr, Yr)
        T["res_m"] = np.hypot(T.E - Xr, T.N - Yr).round(1)
        T["res_dir"] = ((np.degrees(np.arctan2(T.E - Xr, T.N - Yr)) - north) % 360).round()
    f = {"sheet": i, "region": IDX.loc[i, "region"], "place": IDX.loc[i, "place"], "lat": round(lat_c, 4), "lon": round(lon_c, 4),
         "n_coast": int(len(x)), "coast_km": round(len(cp)), "coast_median_m": round(float(np.median(d0))), "coast_p90_m": round(float(np.quantile(d0, .9))),
         "coast_within_250_pct": round(100 * float((d0 <= 250).mean()), 1), "coast_within_500_pct": round(100 * float((d0 <= 500).mean()), 1),
         "coast_within_1000_pct": round(100 * float((d0 <= 1000).mean()), 1),
         "m_per_px": round(scale, 3), "coast_cond": round(float(e0[0] / e0[1]), 2), "rotation_deg": round(((rotg - north + 180) % 360) - 180, 1),
         "n_ctrl": int(len(T)), "n_tie": int((T.source == "tie").sum()) if len(T) else 0, "n_hand": int((T.source == "hand").sum()) if len(T) else 0,
         "w": rec["w"], "h": rec["h"], "coast_hist": np.histogram(np.minimum(d0, 2550), bins=np.arange(0, 2601, 100))[0].tolist()}
    if len(T):
        f["ctrl_rigid_median_m"] = round(float(T.res_m.median()))
    # ---- point fits on the control points: similarity, affine and (12 or more points) quadratic, leave-one-out ----
    if len(T) >= 4:
        xs_, ys_, E_, N_ = T.x.values / 1000, T.y.values / 1000, T.E.values, T.N.values
        def loo(order, sim=False):
            out = []
            for k in range(len(T)):
                m = np.arange(len(T)) != k
                cc = simfit(xs_[m], ys_[m], E_[m], N_[m]) if sim else fit(xs_[m], ys_[m], E_[m], N_[m], order)
                a, b = ev(cc, xs_[k:k + 1], ys_[k:k + 1], 1 if sim else order); out.append(float(np.hypot(a[0] - E_[k], b[0] - N_[k])))
            return np.array(out)
        cs = simfit(xs_, ys_, E_, N_); a, b = ev(cs, xs_, ys_, 1); rs = np.hypot(a - E_, b - N_)
        sc_s, _, rot_s = affine_props((cs[0] * np.r_[1e-3, 1e-3, 1], cs[1] * np.r_[1e-3, 1e-3, 1]))
        f.update({"sim_rms_m": round(float(np.sqrt((rs ** 2).mean()))), "sim_loo_median_m": round(float(np.median(loo(1, True)))),
                  "sim_scale_ratio": round(sc_s / rec["m_per_px_nominal"], 3), "sim_rotation_deg": round(((rot_s - north + 180) % 360) - 180, 1)})
        T["res_sim_m"] = rs.round(1)
        if len(T) >= 6:
            ca = fit(xs_, ys_, E_, N_, 1); a, b = ev(ca, xs_, ys_, 1); ra = np.hypot(a - E_, b - N_)
            sc_a, an_a, _ = affine_props((ca[0] * np.r_[1e-3, 1e-3, 1], ca[1] * np.r_[1e-3, 1e-3, 1]))
            f.update({"aff_rms_m": round(float(np.sqrt((ra ** 2).mean()))), "aff_loo_median_m": round(float(np.median(loo(1)))), "aff_anisotropy": round(an_a, 3)})
        if len(T) >= 12:
            cq = fit(xs_, ys_, E_, N_, 2); a, b = ev(cq, xs_, ys_, 2); rq = np.hypot(a - E_, b - N_)
            f.update({"quad_rms_m": round(float(np.sqrt((rq ** 2).mean()))), "quad_loo_median_m": round(float(np.median(loo(2))))})
    # image corners for the web map (lon, lat): top-left, top-right, bottom-right, bottom-left, from the coastline fit
    W, H = rec["w"], rec["h"]
    Xk, Yk = ev(c0, np.array([0, W, W, 0], float), np.array([0, 0, H, H], float), 1)
    lo, la = TI.transform(Xk, Yk)
    f["corners"] = [[round(a, 5), round(b, 5)] for a, b in zip(lo, la)]
    f["rigid"] = [list(map(float, c0[0])), list(map(float, c0[1]))]
    ties.append(T.drop(columns=["E", "N"]))
    fits[i] = f
    print(i, f["place"], "coast median", f["coast_median_m"], "m;", len(T), "control points (", f["n_tie"], "auto) median", f.get("ctrl_rigid_median_m"),
          "sim loo", f.get("sim_loo_median_m"), "aff loo", f.get("aff_loo_median_m"), "rot", f["rotation_deg"], flush=True)

TP = pd.concat(ties, ignore_index=True)
TP["map_lat"] = TP.map_lat.astype(float).round(5); TP["map_lon"] = TP.map_lon.astype(float).round(5)
TP.to_csv(f"{DATA}/control_fit.csv", index=False)

# ---------- national check on the 1878 map ----------
N = pd.read_csv(f"{DATA}/national_points.csv")
E, Nn = TF.transform(N.lon.values, N.lat.values)
x, y = N.x_1878.values.astype(float), N.y_1878.values.astype(float)
M = np.zeros((2 * len(N), 4)); M[0::2, 0] = x; M[0::2, 1] = y; M[0::2, 2] = 1; M[1::2, 0] = -y; M[1::2, 1] = x; M[1::2, 3] = 1
a, b, c, e = np.linalg.lstsq(M, np.c_[E, Nn].reshape(-1), rcond=None)[0]
Eh, Nh = a * x + b * y + c, b * x - a * y + e
ca = fit(x, y, E, Nn, 1); Ea, Na = ev(ca, x, y, 1)
north = north_angle(E, Nn); t = np.radians(north)
dE_g, dN_g = Eh - E, Nh - Nn                                   # grid components -> true east and north components
dN_t = dN_g * np.cos(t) - dE_g * np.sin(t); dE_t = dE_g * np.cos(t) + dN_g * np.sin(t)
N["dE_km"], N["dN_km"] = (dE_t / 1000).round(2), (dN_t / 1000).round(2)
N["d_km"] = (np.hypot(dE_t, dN_t) / 1000).round(2)
N["dlat_min"] = (dN_t / 1852).round(1); N["dlon_min"] = (dE_t / (1852 * np.cos(np.radians(N.lat)))).round(1)
N.to_csv(f"{DATA}/national_fit.csv", index=False)
def ewns(ix):
    c_ = fit(x[ix], y[ix], E[ix], Nn[ix], 1); M = np.array([[c_[0][0], c_[0][1]], [c_[1][0], c_[1][1]]])
    return np.hypot(*M[:, 0]) / np.hypot(*M[:, 1])
rng = np.random.default_rng(1821)
boot = np.array([ewns(rng.integers(0, len(N), len(N))) for _ in range(2000)])
M_ = np.array([[ca[0][0], ca[0][1]], [ca[1][0], ca[1][1]]])
NAT = {"n": len(N), "km_per_px": float(np.hypot(a, b) / 1000), "rms_EW_km": float(np.sqrt((dE_t ** 2).mean()) / 1000), "rms_NS_km": float(np.sqrt((dN_t ** 2).mean()) / 1000),
       "affine_ew_ns_ratio": float(np.hypot(*M_[:, 0]) / np.hypot(*M_[:, 1])),
       "ratio_ci": [float(np.quantile(boot, .025)), float(np.quantile(boot, .975))],
       "slope_EW_km_per_deg": float(np.polyfit(N.lon, dE_t / 1000, 1)[0]), "slope_NS_km_per_deg": float(np.polyfit(N.lon, dN_t / 1000, 1)[0])}
jsave({"sheets": fits, "national": NAT, "draw_mm": DRAW_MM, "scale": SCALE}, f"{DATA}/fits.json", indent=1)
print("national", {k: round(v, 3) if isinstance(v, float) else v for k, v in NAT.items()})
print(N[["feature", "lon", "dE_km", "dN_km"]].to_string())
