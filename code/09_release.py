"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23882609, https://doi.org/10.5281/zenodo.23882609 and https://blog.tristanhotham.com/2026/10/31/ino-japan/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "05_build_site.py"))
spec.loader.exec_module(importlib.util.module_from_spec(spec))          # shared fact checks
R = jload(f"{DATA}/results.json"); F = jload(f"{DATA}/fits.json")
FS = {int(k): v for k, v in F["sheets"].items()}
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Ino_Japan"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}

# numbers written in words or alt text in the blog and collage
assert R["source"]["located"] == 28 and R["national"]["n"] == 18
assert min(f["coast_median_m"] for f in FS.values()) == 108 and max(f["coast_median_m"] for f in FS.values()) == 651
assert R["expect"]["draw_m"] == 22 and R["coast"]["median_of_sheets_m"] == 280
NF = __import__("pandas").read_csv(f"{DATA}/national_fit.csv")
assert -16.5 < min(NF.dE_km.min(), NF.dN_km.min()) < -14.5 and 12.5 < max(NF.dE_km.max(), NF.dN_km.max()) < 13.6   # "about minus 15 and plus 13 km"

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
from PIL import Image
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
c = R["coast"]
meta = {"title": "How close did Ino get? Japan's first measured map against a modern one",
        "slug": "ino-japan",
        "excerpt": f"A retired sake brewer measured Japan on foot. I laid {R['source']['located']} sheets of his 1821 map on today's coast: a typical sheet's coast sits a median {c['median_of_sheets_m']} m from the modern line.",
        "seo_description": f"Ino Tadataka's 1821 survey map of Japan beside a modern map: {R['source']['located']} sheets, {c['km']:,} km of coast, a median {c['median_of_sheets_m']} m from today's.",
        "tags": ["maps", "history", "Japan", "Hokkaido", "Ino Tadataka", "cartography", "surveying", "data visualisation"],
        "header_alt": f"Title card reading 'Ino's Japan' in black and red on pale paper, beside a modern map of Hokkaido with the coast drawn on Ino's sheets traced in red along the real shoreline. Text: {R['source']['located']} sheets of the 1821 survey map, {c['km']:,} km of drawn coast, a median {c['median_of_sheets_m']} m from today's."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/ino-japan_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"ino-japan/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"ino-japan/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "ino-japan/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&")
zmeta = {"title": "How Close Did Ino Get? Measuring Sheets of Ino Tadataka's Large-Scale Map of Japan (1821) Against the Modern Coastline",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Sources: Library of Congress manuscript copy of the Dai Nihon Enkai Yochi Zenzu and the 1878 Army General Staff map (public domain, via Wikimedia Commons); Natural Earth.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["Ino Tadataka", "historical cartography", "map accuracy", "georeferencing", "Hokkaido", "Edo period", "Japan", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": LOC_URL, "relation": "isDerivedFrom", "resource_type": "image"},
                                 {"identifier": NE_URL, "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
