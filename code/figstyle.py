"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, Natural Earth outlines, and the sheet images."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from PIL import Image
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#68625A", "axes.labelcolor": "#22201C",
                     "xtick.color": "#68625A", "ytick.color": "#68625A"})
# washi paper, sumi ink, vermilion survey lines, indigo sea, the green of Ino's hachured hills
BG, FG, MUT, LAND, RULE, SEA = "#F6F1E6", "#22201C", "#68625A", "#E8E0CC", "#E0D6C1", "#E6ECEE"
RED, BLUE, GREEN, GOLD = "#B8322A", "#2F4F86", "#4E7D5B", "#B07A12"
JP = jload(f"{DATA}/japan.json")
WD = jload(f"{DATA}/world.json")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


def basemap(ax, ext, land=LAND, ec="#FFFFFF", lw=.4, sea=SEA, detail=True):
    """Plate carree with the cosine of the mid latitude as aspect. Natural Earth 1:10m for Japan, 1:50m elsewhere."""
    ax.set_facecolor(sea)
    for f in WD["features"]:
        if detail and f["properties"]["iso"] in ("JPN", "RUS"):
            continue
        for r in rings(f["geometry"]):
            ax.add_patch(MPoly(r, closed=True, fc=land, ec=ec, lw=lw, zorder=1))
    if detail:
        for f in JP["features"]:
            for r in rings(f["geometry"]):
                ax.add_patch(MPoly(r, closed=True, fc=land, ec="none", lw=0, zorder=1))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.set_aspect(1 / np.cos(np.radians((ext[2] + ext[3]) / 2)))
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def sheet_img(i):
    return Image.open(f"{IMG}/sheet_{i}.jpg")
