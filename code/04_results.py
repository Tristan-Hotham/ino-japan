"""Every number used anywhere (data/results.json), the per-sheet table (data/sheet_summary.csv) and the page data
(data/site.json). Reads only data/ (raw/ is not needed from here on)."""
import numpy as np, pandas as pd
from common import *

F = jload(f"{DATA}/fits.json"); FS = {int(k): v for k, v in F["sheets"].items()}
IDX = pd.read_csv(f"{DATA}/sheet_index.csv")
NF = pd.read_csv(f"{DATA}/national_fit.csv")
S = jload(f"{DATA}/sheets.json")
D = pd.DataFrame(FS.values()).sort_values("sheet")
pc = lambda a, b: round(100 * a / b, 1) if b else None
R = {}

loc = IDX[IDX.status == "located"]; nl = IDX[IDX.status != "located"]
R["source"] = {"n_sheets": len(IDX), "total_sheets": TOTAL_SHEETS, "pct_of_set": pc(len(IDX), TOTAL_SHEETS), "located": len(loc),
               "not_located": len(nl), "drafts": int(nl.note.fillna("").str.contains("pencil").sum()),
               "located_pct_of_set": pc(len(loc), TOTAL_SHEETS), "scale": SCALE_HOKKAIDO, "scale_main": SCALE_LARGE,
               "first_sheet": int(IDX.sheet.min()), "last_sheet": int(IDX.sheet.max())}
R["regions"] = {}
for reg, _ in [("Kuril islands", 0), ("Okhotsk coast", 0), ("Nemuro and Kushiro", 0), ("Pacific coast", 0), ("Japan Sea coast", 0), ("Sakhalin", 0)]:
    d = D[D.region == reg]
    R["regions"][reg] = {"sheets": len(d), "coast_median_m": round(float(d.coast_median_m.median())) if len(d) else None,
                         "sheet_list": ", ".join(str(s_) for s_ in d.sheet)}
REG = list(R["regions"])

# ---------- coastline agreement (rigid fit at the nominal scale: one position and one rotation per sheet) ----------
R["coast"] = {"km": int(D.coast_km.sum()), "median_of_sheets_m": round(float(D.coast_median_m.median())),
              "best_sheet": int(D.loc[D.coast_median_m.idxmin(), "sheet"]), "best_m": int(D.coast_median_m.min()), "best_place": D.loc[D.coast_median_m.idxmin(), "place"],
              "worst_sheet": int(D.loc[D.coast_median_m.idxmax(), "sheet"]), "worst_m": int(D.coast_median_m.max()), "worst_place": D.loc[D.coast_median_m.idxmax(), "place"],
              "within250_median_pct": round(float(D.coast_within_250_pct.median())), "within500_median_pct": round(float(D.coast_within_500_pct.median())),
              "within1000_median_pct": round(float(D.coast_within_1000_pct.median())), "sheets_under_300": int((D.coast_median_m < 300).sum()),
              "sheets_over_500": int((D.coast_median_m > 500).sum())}
for reg in REG:
    d = D[D.region == reg]
    R["regions"][reg]["coast_km"] = int(d.coast_km.sum())

# ---------- control points: hand-picked capes and automatic coast windows ----------
C = pd.read_csv(f"{DATA}/control_fit.csv")
H, A_ = C[C.source == "hand"], C[C.source == "tie"]
R["ctrl"] = {"n": int(len(C)), "hand": int(len(H)), "auto": int(len(A_)), "sheets": int(C.sheet.nunique()), "sheets_4": int((D.n_ctrl >= 4).sum()),
             "sheets_8": int((D.n_ctrl >= 8).sum()), "target": 250, "median_m": round(float(C.res_m.median())), "p90_m": round(float(C.res_m.quantile(.9))),
             "hand_median_m": round(float(H.res_m.median())), "auto_median_m": round(float(A_.res_m.median())), "under_500_pct": pc((C.res_m < 500).sum(), len(C)),
             "under_1000_pct": pc((C.res_m < 1000).sum(), len(C)), "max_m": round(float(C.res_m.max())), "high_n": int((H.conf == "high").sum())}
named = {}
for g in H.itertuples():
    if isinstance(g.note, str) and g.note and g.conf == "high":
        named[g.note] = {"res_m": round(float(g.res_m)), "sheet": int(g.sheet)}
R["ctrl"]["named"] = named
sim = D.dropna(subset=["sim_loo_median_m"]); aff = D.dropna(subset=["aff_loo_median_m"]); qd = D.dropna(subset=["quad_loo_median_m"])
R["fitq"] = {"sim_sheets": len(sim), "sim_loo_median_m": round(float(sim.sim_loo_median_m.median())), "sim_rms_median_m": round(float(sim.sim_rms_m.median())),
             "aff_sheets": len(aff), "aff_loo_median_m": round(float(aff.aff_loo_median_m.median())), "sim_loo_on_aff_sheets_m": round(float(aff.sim_loo_median_m.median())),
             "quad_sheets": len(qd), "quad_loo_m": round(float(qd.quad_loo_median_m.median())) if len(qd) else None,
             "aff_loo_on_quad_sheets_m": round(float(qd.aff_loo_median_m.median())) if len(qd) else None,
             "aff_better": int((aff.aff_loo_median_m < aff.sim_loo_median_m).sum())}

# ---------- distortion: rotation and scale ----------
W = D[D.coast_cond >= 0.15]
S4 = sim[(sim.n_ctrl >= 6)]
R["distortion"] = {"rot_n": len(W), "rot_median": round(float(W.rotation_deg.median()), 1), "rot_abs_median": round(float(W.rotation_deg.abs().median()), 1),
                   "rot_min": round(float(W.rotation_deg.min()), 1), "rot_max": round(float(W.rotation_deg.max()), 1),
                   "rot_within2": int((W.rotation_deg.abs() <= 2).sum()),
                   "scale_n": len(S4), "scale_median": round(float(S4.sim_scale_ratio.median()), 3),
                   "scale_min": round(float(S4.sim_scale_ratio.min()), 3), "scale_max": round(float(S4.sim_scale_ratio.max()), 3)}
R["distortion"]["scale_dev_pct"] = round(100 * float((S4.sim_scale_ratio - 1).abs().max()))

# ---------- what the scale allows ----------
R["expect"] = {"draw_mm": F["draw_mm"], "draw_m": round(F["draw_mm"] / 1000 * SCALE_HOKKAIDO), "ri_cm": round(3927.0 / SCALE_HOKKAIDO * 100, 1),
               "px_m": round(float(D.m_per_px.median()), 1)}
R["expect"]["coast_mm"] = round(R["coast"]["median_of_sheets_m"] / SCALE_HOKKAIDO * 1000, 1)
R["expect"]["ctrl_mm"] = round(R["ctrl"]["median_m"] / SCALE_HOKKAIDO * 1000, 1)
R["expect"]["coast_x_draw"] = round(R["coast"]["median_of_sheets_m"] / R["expect"]["draw_m"])

# ---------- national ----------
NA = F["national"]
R["national"] = {"n": NA["n"], "rms_ew_km": round(NA["rms_EW_km"], 1), "rms_ns_km": round(NA["rms_NS_km"], 1), "km_per_px": round(NA["km_per_px"], 2),
                 "ew_ns_ratio": round(NA["affine_ew_ns_ratio"], 3), "ci_lo_pct": round(100 * (1 / NA["ratio_ci"][1] - 1), 1), "ci_hi_pct": round(100 * (1 / NA["ratio_ci"][0] - 1), 1), "slope_ew": round(NA["slope_EW_km_per_deg"], 2), "slope_ns": round(NA["slope_NS_km_per_deg"], 2),
                 "median_km": round(float(NF.d_km.median()), 1), "max_km": round(float(NF.d_km.max()), 1),
                 "max_feature": NF.loc[NF.d_km.idxmax(), "feature"], "dlat_abs_median_min": round(float(NF.dlat_min.abs().median()), 1),
                 "dlon_abs_median_min": round(float(NF.dlon_min.abs().median()), 1)}
R["national"]["ew_stretch_pct"] = round(100 * (1 / NA["affine_ew_ns_ratio"] - 1), 1)    # east-west drawn this much longer than north-south
R["national"]["pick_km"] = round(NA["km_per_px"] * 3, 1)                 # three pixels of picking uncertainty
R["facts"] = {"born": 1745, "died": 1818, "first_survey": 1800, "start_age": 55, "years": 17, "walk_km": 35000, "completed": 1821, "total_sheets": TOTAL_SHEETS,
              "scale_main": SCALE_LARGE, "scale_hokkaido": SCALE_HOKKAIDO}
R["method"] = {"m_per_orig_px": 6.66, "dpi": round(0.0254 * SCALE_HOKKAIDO / 6.66), "window_km": 8, "window_step_km": 3, "tie_cond": 0.10, "rot_cond": 0.15,
               "tie_match_m": 600, "tie_shift_km": 3, "stroke_qpx": 40, "rot_range": 15, "rot_step": 3, "grid_km": 1, "width_px": 3840,
               "nat_w": 1885, "boot": 2000, "islands": int((NF.kind == "island").sum())}
R["meta"] = {"page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "slug": SLUG, "loc": LOC_URL}

# ---------- tables ----------
cols = ["sheet", "region", "place", "lat", "lon", "coast_km", "coast_median_m", "coast_p90_m", "coast_within_500_pct", "coast_cond", "rotation_deg",
        "n_ctrl", "n_hand", "n_tie", "ctrl_rigid_median_m", "sim_rms_m", "sim_loo_median_m", "sim_scale_ratio", "sim_rotation_deg", "aff_rms_m", "aff_loo_median_m", "quad_loo_median_m"]
D.reindex(columns=cols).to_csv(f"{DATA}/sheet_summary.csv", index=False)

# ---------- page data ----------
sheets = []
for r in IDX.itertuples():
    i = int(r.sheet); s_ = S[str(i)]; k = 1600 / max(s_["w"], s_["h"])
    e = {"id": i, "status": r.status, "region": r.region if isinstance(r.region, str) else "", "place": r.place if isinstance(r.place, str) else "",
         "note": r.note if isinstance(r.note, str) else "", "img": f"img/sheet_{i}.jpg", "w": round(s_["w"] * k), "h": round(s_["h"] * k)}
    if i in FS:
        f = FS[i]
        e.update({k_: f.get(k_) for k_ in ("lat", "lon", "corners", "coast_km", "coast_median_m", "coast_within_500_pct", "coast_cond", "rotation_deg",
                                           "n_ctrl", "ctrl_rigid_median_m", "sim_loo_median_m", "sim_scale_ratio")})
        e = {k_: (None if isinstance(v, float) and np.isnan(v) else v) for k_, v in e.items()}
        c = C[C.sheet == i]
        e["pts"] = [[p.id, p.source, p.kind, p.conf, p.note if isinstance(p.note, str) else "", round(p.x * k, 1), round(p.y * k, 1), p.lat, p.lon, p.map_lat, p.map_lon,
                     round(p.res_m), int(p.res_dir)] for p in c.itertuples()]
    sheets.append(e)
site = {"sheets": sheets, "regions": [[k_, RCOL.get(k_, "#888")] for k_ in REG],
        "pt_cols": ["id", "source", "kind", "conf", "note", "x", "y", "lat", "lon", "map_lat", "map_lon", "res_m", "res_dir"],
        "national": NF[["feature", "kind", "x_1878", "y_1878", "lat", "lon", "dE_km", "dN_km", "d_km"]].values.tolist(),
        "nat_img": {"src": "img/whole1878.jpg", "w": 1885, "h": 1782},
        "coast_hist": np.sum([f["coast_hist"] for f in FS.values()], axis=0).tolist(),
        "ctrl_hist": np.histogram(np.minimum(C.res_m, 2550), bins=np.arange(0, 2601, 100))[0].tolist()}
jsave(site, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: R[k] for k in ("source", "coast", "ctrl", "fitq", "distortion", "expect", "national")}, indent=0)[:5000])
print(pd.DataFrame(R["regions"]).T)
