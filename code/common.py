"""Shared paths, constants and helpers for the ino-japan project.

Raw inputs (raw/, read in place, never modified; steps 04 onward and the release run without raw/):
  raw/sheets/sheet_2001620020-N.jpg (N = 1 to 40)
      Dai Nihon Enkai Yochi Zenzu, large-scale sheets 1 to 40 of the manuscript copy held by the Library of Congress
      (Geography and Map Division, call number G7960 1821 .I5, item 2001620020). Public domain. Downloaded from
      Wikimedia Commons ("Dai Nihon enkai yochi zenzu LOC 2001620020-N.jpg") and reduced to 3,840 px wide.
  raw/commons_meta.json        Wikimedia Commons file descriptions and original pixel sizes for those files.
  raw/japan_ino_1878_whole.jpg  "Dai Nihon Zenzu", Army General Staff Bureau, 1878, a whole-Japan map compiled from
                                Ino's survey (Wikimedia Commons, public domain), 1,885 px.
  raw/inoh_taizu_replica_all_sheets.jpg  photograph of a full-size replica of the large sheets laid out on a floor
                                (Wikimedia Commons, "Inoh taizu 01.jpg"). Shown on the page for context only.
  /home/claude/newdata/raw/geo/ne_10m_admin_0_countries.geojson   Natural Earth 1:10m countries (public domain): the
                                modern coastline of Japan and the islands now administered by Russia.
  /home/claude/newdata/raw/geo/ne_50m_admin_0_countries.geojson   Natural Earth 1:50m, for small overview maps.
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("INO_RAW", os.path.join(ROOT, "raw"))
GEO = os.environ.get("INO_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("INO_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
WORK = os.path.join(os.environ.get("INOTMP", "/dev/shm/inojapan"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK, IMG):
    os.makedirs(d, exist_ok=True)

SLUG = "ino-japan"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23882609"                       # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/ino-japan/"                 # filled in by the publisher
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
LOC_URL = "https://www.loc.gov/item/2001620020/"
COMMONS_SHEET = "https://commons.wikimedia.org/wiki/File:Dai_Nihon_enkai_yochi_zenzu_LOC_2001620020-{n}.jpg"
COMMONS_1878 = "https://commons.wikimedia.org/wiki/Category:Ino_maps"
COMMONS_REPLICA = "https://commons.wikimedia.org/wiki/File:Inoh_taizu_01.jpg"
NE_URL = "https://www.naturalearthdata.com/"

# map projection used for all measurements: Lambert conformal conic fitted to Japan (metres)
LCC = "+proj=lcc +lat_1=33 +lat_2=44 +lat_0=38 +lon_0=138 +units=m +ellps=WGS84"
SCALE_LARGE, SCALE_HOKKAIDO = 36000, 43600
QPX = 4                               # sheets are analysed at a quarter of the 3,840 px images
TOTAL_SHEETS = 214                    # the complete large-scale set (LoC description)

# groups of sheets for the page and figures, in survey order around the coast
REGIONS = [("Kuril islands", "#6E4C9A"), ("Okhotsk coast", "#2F5FA7"), ("Nemuro and Kushiro", "#2E8A6E"),
           ("Pacific coast", "#C2412D"), ("Japan Sea coast", "#B07A12"), ("Sakhalin", "#5D8F9E")]
RCOL = dict(REGIONS)


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "wt", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "k": return f"{float(v) / 1000:.1f}"
    raise ValueError(f)


def proj():
    from pyproj import Transformer
    return (Transformer.from_crs(4326, LCC, always_xy=True), Transformer.from_crs(LCC, 4326, always_xy=True))


def gc_km(lat1, lon1, lat2, lon2):
    import numpy as np
    p1, p2, l1, l2 = map(np.radians, (lat1, lat2, lon1, lon2))
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2))

# modern towns and capes used only to name the area each sheet covers (approximate positions)
TOWNS = [("Wakkanai", 45.42, 141.67), ("Sarufutsu", 45.33, 142.11), ("Hamatonbetsu", 45.12, 142.39), ("Esashi (Okhotsk)", 44.94, 142.58),
         ("Omu", 44.58, 142.96), ("Monbetsu", 44.35, 143.35), ("Lake Saroma", 44.15, 143.85), ("Abashiri", 44.02, 144.27),
         ("Shari", 43.91, 144.67), ("Rausu", 44.02, 145.19), ("Notsuke", 43.58, 145.30), ("Nemuro", 43.33, 145.58),
         ("Akkeshi", 43.04, 144.85), ("Kushiro", 42.98, 144.38), ("Tokachi", 42.70, 143.55), ("Hiroo", 42.29, 143.31),
         ("Cape Erimo", 41.93, 143.25), ("Urakawa", 42.17, 142.77), ("Shizunai", 42.33, 142.37), ("Tomakomai", 42.63, 141.60),
         ("Muroran", 42.32, 140.97), ("Hakodate", 41.77, 140.73), ("Setana", 42.45, 139.85), ("Iwanai", 42.98, 140.51),
         ("Shakotan", 43.30, 140.50), ("Otaru", 43.19, 141.00), ("Ishikari", 43.17, 141.32), ("Mashike", 43.85, 141.52),
         ("Rumoi", 43.94, 141.64), ("Haboro", 44.36, 141.70), ("Teshio", 44.88, 141.75), ("Rishiri and Rebun", 45.25, 141.15),
         ("Kunashiri", 44.05, 145.80), ("Iturup (Etorofu)", 44.95, 147.60), ("southern Sakhalin", 46.30, 141.90)]
