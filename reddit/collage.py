"""Reddit collage (2400 x 3200): the located sheets back on a modern map of Hokkaido, one sheet beside the modern coast,
and the headline numbers. Light background; labels sit on plain sea or paper; numbers from data/results.json."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Polygon as MP, FancyArrowPatch
from figstyle import *

R = jload(f"{DATA}/results.json"); F = jload(f"{DATA}/fits.json"); S = jload(f"{DATA}/sheets.json")
FS = {int(k): v for k, v in F["sheets"].items()}
C = pd.read_csv(f"{DATA}/control_fit.csv")
TF, TI = proj()
HALO = [pe.withStroke(linewidth=3, foreground=SEA)]


def old_coast(i):
    P = np.array(S[str(i)]["coast_px"], float); A = FS[i]["rigid"]
    return TI.transform(A[0][0] * P[:, 0] + A[0][1] * P[:, 1] + A[0][2], A[1][0] * P[:, 0] + A[1][1] * P[:, 1] + A[1][2])


fig = plt.figure(figsize=(8, 32 / 3), dpi=300, facecolor=BG)
fig.text(.05, .957, "How close did Ino get?", fontproperties=DISP, fontsize=30, color=RED)
fig.text(.05, .93, "Japan's first measured map (1821), laid on today's coast", fontproperties=DISPB, fontsize=14, color=FG)
fig.text(.05, .911, f"A retired sake brewer walked the coast with a measuring chain from {R['facts']['first_survey']}. These are the {R['source']['located']} sheets of", fontsize=7.6, color=MUT)
fig.text(.05, .899, "his large-scale map photographed by the Library of Congress that I could place: the far north.", fontsize=7.6, color=MUT)

# big map
a = fig.add_axes([.03, .5, .94, .39]); basemap(a, (139.2, 148.6, 41.55, 46.75))
for i, f in FS.items():
    c = np.array(f["corners"]); a.add_patch(MP(c, closed=True, fc=RCOL[f["region"]], alpha=.13, ec=RCOL[f["region"]], lw=.6, zorder=3))
    lo, la = old_coast(i); a.scatter(lo, la, s=.25, c=RED, lw=0, zorder=4)
for t, lo, la in (("Sea of Japan", 139.75, 44.45), ("Sea of Okhotsk", 144.3, 45.7), ("Pacific Ocean", 145.6, 42.1), ("Cape Erimo", 143.75, 41.78),
                  ("Kunashiri", 146.75, 43.75), ("Sakhalin", 142.9, 46.55), ("Rishiri", 140.45, 45.55), ("Nemuro", 146.25, 43.2)):
    a.text(lo, la, t, ha="center", va="center", fontsize=8 if "Sea" in t or "Ocean" in t else 6.6, color=BLUE if ("Sea" in t or "Ocean" in t) else FG,
           fontstyle="italic" if ("Sea" in t or "Ocean" in t) else "normal", path_effects=HALO, zorder=8)
fig.legend(handles=[Line2D([], [], color=RED, lw=2, label="coast as drawn on the sheets"), Patch(fc=LAND, ec="#BFB49C", label="land today (Natural Earth)")] +
           [Patch(fc=RCOL[r], alpha=.4, ec=RCOL[r], label=f"sheet footprints: {r}") for r, _ in REGIONS],
           loc="upper left", bbox_to_anchor=(.03, .495), ncol=2, frameon=False, fontsize=6.6)

# one sheet: as drawn and placed
I = 6; f = FS[I]; im = sheet_img(I); k = im.size[0] / f["w"]
a1 = fig.add_axes([.04, .2, .44, .2]); a1.imshow(im); a1.axis("off")
p = C[C.sheet == I]
a2 = fig.add_axes([.52, .2, .44, .2]); cc = np.array(f["corners"])
basemap(a2, (cc[:, 0].min(), cc[:, 0].max(), cc[:, 1].min(), cc[:, 1].max()))
lo, la = old_coast(I); a2.scatter(lo, la, s=.8, c=RED, lw=0, zorder=4)
fig.text(.04, .405, f"Sheet {I}: the Nemuro peninsula as drawn", fontproperties=DISPB, fontsize=9.5, color=FG)
fig.text(.52, .405, "...and its coast (red) on today's map", fontproperties=DISPB, fontsize=9.5, color=FG)
fig.text(.52, .19, f"median gap {f['coast_median_m']} m after one shift and one turn", fontsize=6.8, color=MUT)

# numbers
st = [(f"{R['coast']['median_of_sheets_m']} m", "median gap between a sheet's drawn\ncoast and today's coast", RED),
      (f"{R['coast']['within1000_median_pct']}%", "of a typical sheet's coast is within\na kilometre of the modern line", BLUE),
      (f"{R['coast']['km']:,} km", "of drawn coast measured, Hokkaido,\nthe Kurils and Sakhalin", GREEN),
      (f"{R['distortion']['rot_abs_median']}°", "median tilt from true north, on\nsheets whose coast fixes the angle", GOLD)]
for n_, (big, small, col) in enumerate(st):
    x = .05 + (n_ % 2) * .46; y = .165 - (n_ // 2) * .06
    fig.text(x, y, big, fontproperties=DISP, fontsize=19, color=col, va="top")
    fig.text(x + .2, y - .004, small, fontsize=6.6, color=FG, va="top", linespacing=1.35)
fig.text(.05, .036, f"Upper bounds: the gaps include copying, paper and the generalised modern outline. {R['source']['n_sheets']} of {R['facts']['total_sheets']} sheets, far north only.", fontsize=5.9, color=MUT)
fig.text(.05, .025, "Sources: Library of Congress copy of Ino's Dai Nihon Enkai Yochi Zenzu (public domain, via Wikimedia Commons); Natural Earth.", fontsize=5.9, color=MUT)
fig.text(.05, .014, "Dr Tristan Hotham · maps.tristanhotham.com/ino-japan", fontsize=5.9, color=MUT)
out = os.path.join(ROOT, "reddit", "ino_japan_collage.png")
fig.savefig(out, dpi=300, facecolor=BG); plt.close(fig)
from PIL import Image
assert Image.open(out).size == (2400, 3200), Image.open(out).size
print("collage", out)
