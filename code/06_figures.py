"""Header card, blog figures (release/blog/b_*.png, 1800 px wide) and paper figures (release/paper/f_*.png).
Numbers from data/results.json; positions from data/fits.json, data/sheets.json and data/control_fit.csv."""
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, FancyArrowPatch, Polygon as MP
from figstyle import *

R = jload(f"{DATA}/results.json"); F = jload(f"{DATA}/fits.json"); S = jload(f"{DATA}/sheets.json")
FS = {int(k): v for k, v in F["sheets"].items()}
C = pd.read_csv(f"{DATA}/control_fit.csv"); NF = pd.read_csv(f"{DATA}/national_fit.csv")
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
TF, TI = proj()
HALO = [pe.withStroke(linewidth=3, foreground=SEA)]
HALOP = [pe.withStroke(linewidth=3, foreground=BG)]
REGS = [r for r, _ in REGIONS]


def both(fig, name, blog=True):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def old_coast(i):
    """drawn coast of sheet i placed by the coastline fit, as lon, lat"""
    P = np.array(S[str(i)]["coast_px"], float); A = FS[i]["rigid"]
    X = A[0][0] * P[:, 0] + A[0][1] * P[:, 1] + A[0][2]; Y = A[1][0] * P[:, 0] + A[1][1] * P[:, 1] + A[1][2]
    return TI.transform(X, Y)


def footprint(ax, i, col, lw=1.0, label=True, fs=7):
    c = np.array(FS[i]["corners"])
    ax.add_patch(MP(c, closed=True, fc=col, alpha=.10, ec=col, lw=lw, zorder=3))
    if label:
        ax.text(c[:, 0].mean(), c[:, 1].mean(), str(i), ha="center", va="center", fontsize=fs, color=col, zorder=6, path_effects=HALO)


# ---------- 1. overview: every located sheet back in place ----------
EXT = (139.3, 148.4, 41.6, 46.6)
fig = plt.figure(figsize=(12, 7.6), facecolor=BG); ax = fig.add_axes([.01, .02, .7, .86])
basemap(ax, EXT)
for i, f in FS.items():
    col = RCOL[f["region"]]
    footprint(ax, i, col, label=False)
    lo, la = old_coast(i); ax.scatter(lo, la, s=.5, c=RED, lw=0, zorder=4)
for i, f in FS.items():
    c = np.array(f["corners"]); ax.text(c[:, 0].mean(), c[:, 1].mean(), str(i), ha="center", va="center", fontsize=7.5, color=RCOL[f["region"]], zorder=6, path_effects=HALO)
fig.text(.02, .935, f"{R['source']['located']} of the {R['source']['n_sheets']} sheets, put back in place on a modern map", fontproperties=DISPB, fontsize=17, color=FG)
fig.text(.02, .9, "Shaded boxes: each sheet's footprint after the fit, numbered. Red: the coast as drawn on the sheet.", fontsize=9.5, color=MUT)
lg = [Patch(fc=RCOL[r], alpha=.35, ec=RCOL[r], label=f"{r} ({R['regions'][r]['sheets']})") for r in REGS] + [Line2D([], [], color=RED, lw=2, label="coast as drawn")]
fig.legend(handles=lg, loc="upper left", bbox_to_anchor=(.72, .82), frameon=False, fontsize=10)
fig.text(.725, .36, f"{R['coast']['km']:,} km of drawn coast\nmeasured against Natural Earth.\n\nThe other {R['source']['not_located']} sheets are blank,\nunfinished pencil drafts or\ntoo slight to place.", fontsize=10, color=FG, va="top", linespacing=1.4)
both(fig, "overview")

# ---------- 2. one sheet beside the modern map ----------
I = 6
f = FS[I]; im = sheet_img(I); k = im.size[0] / f["w"]
fig = plt.figure(figsize=(12, 6.2), facecolor=BG)
a1 = fig.add_axes([.01, .08, .48, .78]); a1.imshow(im); a1.axis("off")
a2 = fig.add_axes([.51, .08, .48, .78])
c = np.array(f["corners"]); ext = (c[:, 0].min() - .02, c[:, 0].max() + .02, c[:, 1].min() - .02, c[:, 1].max() + .02)
basemap(a2, ext)
lo, la = old_coast(I); a2.scatter(lo, la, s=1.2, c=RED, lw=0, zorder=4)
p = C[C.sheet == I]
a1.scatter(p.x * k, p.y * k, s=30, facecolors="none", edgecolors=BLUE, linewidths=1.4, zorder=5)
for r in p.itertuples():
    a2.add_patch(FancyArrowPatch((r.map_lon, r.map_lat), (r.lon, r.lat), arrowstyle="-|>", mutation_scale=8, color=BLUE, lw=1.2, zorder=5))
a2.scatter(p.lon, p.lat, s=18, c=BLUE, zorder=6, edgecolors="white", linewidths=.6)
fig.text(.01, .93, f"Sheet {I}, {f['place']}: as drawn (left) and placed on today's coast (right)", fontproperties=DISPB, fontsize=16, color=FG)
fig.text(.51, .045, f"Red: the drawn coast after one shift and one turn (median gap {f['coast_median_m']} m).", fontsize=8.6, color=MUT)
fig.text(.51, .015, "Blue: control points; arrows run from where the sheet puts them to where they are.", fontsize=8.6, color=MUT)
both(fig, "sheet")

# ---------- 3. coast agreement by sheet ----------
D = pd.DataFrame(FS.values()).sort_values("coast_median_m")
fig, ax = plt.subplots(figsize=(12, 6.4), facecolor=BG); ax.set_facecolor(BG); fig.subplots_adjust(left=.27, right=.97, top=.86, bottom=.1)
for n, r in enumerate(D.itertuples()):
    ax.barh(n, r.coast_median_m, color=RCOL[r.region], height=.7)
    ax.text(r.coast_median_m + 8, n, f"{r.coast_median_m}", va="center", fontsize=8.5, color=FG)
ax.set_yticks(range(len(D))); ax.set_yticklabels([f"{r.sheet}  {r.place}" for r in D.itertuples()], fontsize=8.2); ax.tick_params(axis="y", length=0)
ax.axvline(R["expect"]["draw_m"], color=FG, lw=1, ls=":"); ax.text(R["expect"]["draw_m"] + 6, len(D) - .2, f"{R['expect']['draw_m']} m = half a millimetre on the sheet", fontsize=8.5, color=MUT, va="bottom")
ax.axvline(R["coast"]["median_of_sheets_m"], color=RED, lw=1.2); ax.text(R["coast"]["median_of_sheets_m"] + 6, 1, f"median {R['coast']['median_of_sheets_m']} m", fontsize=9, color=RED)
spines(ax); ax.spines["left"].set_visible(False); ax.set_xlabel("median distance from the drawn coast to today's coast (m)"); ax.grid(axis="x", color=RULE); ax.set_axisbelow(True)
fig.legend(handles=[Patch(color=RCOL[r], label=r) for r in REGS], loc="upper right", bbox_to_anchor=(.97, .92), ncol=3, frameon=False, fontsize=9)
fig.text(.02, .935, "How close each sheet's coast sits to today's", fontproperties=DISPB, fontsize=17, color=FG)
both(fig, "coast")

# ---------- 4. distribution: coast points and control points ----------
hist = np.sum([f["coast_hist"] for f in FS.values()], axis=0)
fig, ax = plt.subplots(figsize=(12, 5.6), facecolor=BG); ax.set_facecolor(BG); fig.subplots_adjust(left=.08, right=.97, top=.84, bottom=.13)
bins = np.arange(0, 2601, 100)
ax.bar(bins[:-1] + 50, hist / hist.sum() / 100, width=100, color=RED, alpha=.75, label="every drawn coast point (distance to today's coast)")
ax.hist(C.res_m.clip(upper=2550), bins=bins, histtype="step", color=BLUE, lw=2, density=True, label=f"{R['ctrl']['n']} control points (distance to the true position)")
ax.axvline(R["expect"]["draw_m"], color=FG, ls=":", lw=1)
ax.set_xlabel("metres"); ax.set_yticks([]); spines(ax); ax.spines["left"].set_visible(False); ax.legend(frameon=False, fontsize=10, loc="upper right")
fig.text(.02, .93, f"Mostly within half a kilometre: {R['coast']['within500_median_pct']}% of a typical sheet's coast, {R['ctrl']['under_500_pct']:.0f}% of control points", fontproperties=DISPB, fontsize=16, color=FG)
both(fig, "spread")

# ---------- 5. national check on the 1878 map ----------
img = Image.open(f"{IMG}/whole1878.jpg")
fig = plt.figure(figsize=(12, 6.6), facecolor=BG)
a1 = fig.add_axes([.01, .03, .5, .85]); a1.imshow(img); a1.axis("off"); a1.set_xlim(150, 1880); a1.set_ylim(1720, 60)
X10 = 10
for r in NF.itertuples():
    a1.add_patch(FancyArrowPatch((r.x_1878, r.y_1878), (r.x_1878 - X10 * r.dE_km / R["national"]["km_per_px"], r.y_1878 + X10 * r.dN_km / R["national"]["km_per_px"]),
                                 arrowstyle="-|>", mutation_scale=9, color=RED, lw=1.5, zorder=5))
    a1.scatter([r.x_1878], [r.y_1878], s=14, c=RED, zorder=6)
a2 = fig.add_axes([.6, .14, .37, .66]); a2.set_facecolor(BG)
a2.scatter(NF.lon, NF.dE_km, s=40, c=BLUE, label="east-west error", zorder=3)
a2.scatter(NF.lon, NF.dN_km, s=40, c=GOLD, marker="s", label="north-south error", zorder=3)
a2.axhline(0, color=FG, lw=.8); spines(a2); a2.grid(color=RULE); a2.set_axisbelow(True)
a2.set_xlabel("longitude (degrees east)"); a2.set_ylabel("km"); a2.legend(frameon=False, fontsize=9.5, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2)
fig.text(.01, .935, f"The whole country, 1878: capes and islands a median {R['national']['median_km']} km from the best fit", fontproperties=DISPB, fontsize=16, color=FG)
fig.text(.01, .9, f"Arrows: from the map's position to the true one, drawn {X10} times longer. {R['national']['n']} points picked by eye; one pixel is {R['national']['km_per_px']} km.", fontsize=9, color=MUT)
both(fig, "national")

# ---------- 6. Cape Erimo and Nemuro close up ----------
fig = plt.figure(figsize=(12, 6.0), facecolor=BG)
for n, (I, title) in enumerate(((24, "Sheet 24, Cape Erimo"), (21, "Sheet 21, Akkeshi"))):
    ax = fig.add_axes([.01 + n * .5, .05, .48, .82]); f = FS[I]; lo, la = old_coast(I)
    ext = (np.min(lo) - .05, np.max(lo) + .05, np.min(la) - .04, np.max(la) + .04)
    basemap(ax, ext); ax.scatter(lo, la, s=1.4, c=RED, lw=0, zorder=4)
    p = C[C.sheet == I]
    for r in p.itertuples():
        ax.add_patch(FancyArrowPatch((r.map_lon, r.map_lat), (r.lon, r.lat), arrowstyle="-|>", mutation_scale=9, color=BLUE, lw=1.3, zorder=5))
    ax.scatter(p.lon, p.lat, s=20, c=BLUE, zorder=6, edgecolors="white", linewidths=.6)
    ax.set_title(f"{title}: median gap {f['coast_median_m']} m", fontproperties=DISPB, fontsize=13, color=FG, loc="left")
fig.text(.01, .94, "Close up: the drawn coast (red) on today's land", fontproperties=DISPB, fontsize=16, color=FG)
both(fig, "closeup")

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
a1 = fig.add_axes([.5, .02, .49, .96]); basemap(a1, (139.4, 148.3, 41.7, 46.5))
for i in FS:
    lo, la = old_coast(i); a1.scatter(lo, la, s=.35, c=RED, lw=0, zorder=4)
fig.text(.04, .78, "Ino's", fontproperties=DISP, fontsize=60, color=FG)
fig.text(.04, .62, "Japan", fontproperties=DISP, fontsize=60, color=RED)
fig.text(.045, .5, "How close did a retired sake brewer", fontproperties=SERP, fontsize=18, color=FG)
fig.text(.045, .44, "with a measuring chain get?", fontproperties=SERP, fontsize=18, color=FG)
fig.text(.045, .3, f"{R['source']['located']} sheets of the 1821 survey map", fontsize=12, color=MUT)
fig.text(.045, .25, f"{R['coast']['km']:,} km of drawn coast, a median {R['coast']['median_of_sheets_m']} m from today's", fontsize=12, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG); plt.close(fig)
assert Image.open(os.path.join(ROOT, "header.png")).size == (1200, 630)
print("figures", sorted(os.listdir(BL)))
