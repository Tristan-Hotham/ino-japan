"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
s, c, k, q, d, n, f = R["source"], R["coast"], R["ctrl"], R["fitq"], R["distortion"], R["national"], R["facts"]
readme = f"""# Ino's Japan: how close did the survey map of 1821 get?

Ino Tadataka's large-scale survey map of Japan (Dai Nihon Enkai Yochi Zenzu, completed {f['completed']}) set against a modern map. The {s['n_sheets']} sheets of the Library of Congress manuscript copy that are photographed on Wikimedia Commons (sheets 1 to {s['last_sheet']}, all in the far north at 1:{f['scale_hokkaido']:,}) are placed on the modern coast by matching their drawn coastlines; {s['located']} are located, and their coastlines, control points, rotation and scale are measured. A whole-Japan map of 1878 compiled from the survey gives a national check of latitude and longitude.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Coverage: {s['n_sheets']} of {f['total_sheets']} sheets ({s['pct_of_set']}%), all Hokkaido, the southern Kurils and Sakhalin; {s['located']} placed, {s['drafts']} unfinished pencil drafts and {s['not_located'] - s['drafts']} others too slight to place.
- Coastline: after one shift and one rotation per sheet at the nominal scale, the drawn coast of a typical sheet is a median {c['median_of_sheets_m']} m from Natural Earth's 1:10m coast ({R['expect']['coast_mm']} mm on the paper); {c['within500_median_pct']}% within 500 m and {c['within1000_median_pct']}% within 1 km; {c['km']:,} km of drawn coast measured. Best sheet {c['best_sheet']} ({c['best_place']}, {c['best_m']} m), worst {c['worst_sheet']} ({c['worst_place']}, {c['worst_m']} m).
- Control points: {k['n']} ({k['hand']} picked by eye, {k['auto']} automatic coast windows) on {k['sheets']} sheets, a median {k['median_m']} m from their true positions; {k['under_1000_pct']:.0f}% within 1 km. Fewer than the {k['target']} aimed for.
- Fits: similarity leave-one-out median {q['sim_loo_median_m']} m on {q['sim_sheets']} sheets; affine {q['aff_loo_median_m']} m against {q['sim_loo_on_aff_sheets_m']} m on {q['aff_sheets']} sheets; quadratic {q['quad_loo_m']} m against {q['aff_loo_on_quad_sheets_m']} m on {q['quad_sheets']} sheets. No sign of distortion within sheets beyond shift, rotation and scale.
- Rotation and scale: median absolute rotation from true north {d['rot_abs_median']} degrees on {d['rot_n']} sheets whose coast fixes the angle; scales {d['scale_min']} to {d['scale_max']} of nominal on {d['scale_n']} well-controlled sheets.
- National (1878 map): {n['n']} capes and islands a median {n['median_km']} km from a best-fitting modern position; root mean square error {n['rms_ns_km']} km north-south and {n['rms_ew_km']} km east-west; east-west scale {n['ew_stretch_pct']}% longer than north-south (95% interval {n['ci_lo_pct']} to {n['ci_hi_pct']}%).
- All distances are upper bounds on survey error: they include copying, paper distortion, picking and the generalisation of the modern coast.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/05_build_site.py`; page data embedded; sheet images in `img/`). |
| `header.png` | Social card, 1200 x 630. |
| `img/sheet_N.jpg` | The 40 sheets, 1,600 px on the long side (Library of Congress, public domain). `img/whole1878.jpg` the 1878 map; `img/replica.jpg` a photograph of a full-size replica. |
| `data/sheet_index.csv` | Hand-checked table of all 40 sheets: placed or not, region, area, starting position and rotation for the fit, reason when not placed (input). |
| `data/control_points.csv` | The {k['hand']} control points I picked by eye: sheet pixel, modern position on Natural Earth's coast, confidence (input). |
| `data/national_points.csv` | The {n['n']} features picked on the 1878 map with modern positions (input). |
| `data/sheets.json` | Every sheet's extracted coast (sheet pixels, one point per 8 px cell) and its rigid coastline fit. |
| `data/fits.json` | Per-sheet fits and measures, image corners for the web map, national fit. |
| `data/control_fit.csv` | All {k['n']} control points with their errors. |
| `data/national_fit.csv` | The 1878 points with east-west and north-south errors. |
| `data/sheet_summary.csv` | One row per located sheet. |
| `data/results.json`, `data/site.json`, `data/japan.json`, `data/world.json` | Every number used; page data; Natural Earth outlines. |
| `code/` | Scripts, run in order, page, paper and blog templates, `qa.js`. |
| `release/` | Paper (`paper/`), blog post and figures (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Drawn coast: dark or red ink next to green hachures, in strokes long enough not to be labels, at a quarter of the 3,840 px resolution.
- Placement: brute-force FFT search of position, rotation and scale against Natural Earth land and sea (`code/02_locate.py search`, about two hours), checked by eye; then a trimmed iterative closest point fit of rotation and translation with the nominal scale (calibrated on sheet 5 and carried to the others by photograph size).
- Coastline agreement: distance from every drawn coast point to the modern coast after the fit; checkpoints every kilometre.
- Control points: capes picked by eye, and coast windows {R['method']['window_km']} km across matched by local translation where the coast curves enough; errors against the coastline fit, which does not use them; similarity, affine and quadratic fits with leave-one-out errors.
- National: similarity and affine fits of {n['n']} picked points on the 1878 map; north-south and east-west residuals; bootstrap of the scale ratio.
- Caveats: 40 of 214 sheets, far north only; Natural Earth 1:10m is generalised; copy and paper distortion; few control points; scale calibrated on one sheet; the 1878 projection is unknown.

## How to rerun

Needs Python 3 with numpy, pandas, scipy, shapely, pyproj, matplotlib, Pillow and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Step 02 reads `raw/` (not published: the 40 sheet photographs, the 1878 map, the replica photograph and `commons_meta.json`); Natural Earth comes from `/home/claude/newdata/raw/geo/`. From step 03 on only `data/` and `img/` (and Natural Earth for step 03) are needed. Intermediate files go to `/dev/shm/inojapan/work` (set `INOTMP` to change).

```
python3 code/01_geo.py          # Natural Earth outlines and dense coast
python3 code/02_locate.py       # drawn coasts, rigid fits, web images (add search to redo the placement search)
python3 code/03_fit.py          # coastline agreement, control points, fits, national check
python3 code/04_results.py      # results.json, tables, page data
python3 code/05_build_site.py   # index.html
python3 code/06_figures.py      # header, blog and paper figures
python3 code/07_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/08_readme.py       # README, LICENSE, Reddit post
python3 code/09_release.py      # blog post, Zenodo files
```

## Sources and licences

- Ino Tadataka and team, Dai Nihon Enkai Yochi Zenzu, large-scale sheets 1 to {s['last_sheet']}, manuscript copy, Library of Congress Geography and Map Division, item 2001620020 ({LOC_URL}). Public domain; photographs via Wikimedia Commons ("Dai Nihon enkai yochi zenzu LOC 2001620020-N.jpg").
- Dai Nihon Zenzu, Army General Staff Bureau, 1878, Wikimedia Commons, public domain.
- Replica photograph: Wikimedia Commons, "Inoh taizu 01.jpg" ({COMMONS_REPLICA}).
- Natural Earth 1:10m and 1:50m countries (public domain). Optional relief tiles on the page: Esri.

## Citation

Hotham, T. (2026) Ino's Japan: how close did the survey map of 1821 get? Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/rocket-launches/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence covers")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0. The map images in img/ (the
Library of Congress copy of Ino Tadataka's Dai Nihon Enkai Yochi Zenzu, the
1878 Army General Staff map, and the replica photograph, all from Wikimedia
Commons) are in the public domain. Natural Earth data are public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] A retired sake brewer walked Japan with a measuring chain from {f['first_survey']}. I laid {s['located']} sheets of his 1821 map on a modern map: the drawn coast sits a median {c['median_of_sheets_m']} m from today's

## Body

Ino Tadataka started surveying Japan at {f['start_age']}, after retiring from the family sake business. Over {f['years']} years his teams walked about {f['walk_km']:,} km of coast and road, and in {f['completed']} the survey became the first map of the whole country drawn from measurement. The Library of Congress holds a copy of the large sheets; I used the {s['n_sheets']} photographed on Wikimedia Commons, which all show Hokkaido, the southern Kurils and Sakhalin. I found where each sheet belongs by matching its drawn coastline to the modern one, then let each move and turn once (no stretching). Across {c['km']:,} km of drawn coast, a typical sheet's coast sits a median {c['median_of_sheets_m']} m from Natural Earth's coastline, {c['within1000_median_pct']}% of it within a kilometre, and the sheets point a median {d['rot_abs_median']} degrees away from true north. Caveats: only {s['pct_of_set']:.0f}% of the {f['total_sheets']} sheets, all in the far north; the modern outline I compared against is itself generalised, so these are upper bounds. Interactive side-by-side map: {PAGE}

## Source comment

Sources: Ino Tadataka's Dai Nihon Enkai Yochi Zenzu, Library of Congress manuscript copy, sheets 1 to {s['last_sheet']} (public domain, photographs via Wikimedia Commons); the 1878 Army General Staff map of Japan (Wikimedia Commons, public domain); Natural Earth 1:10m coastline.

Tools: Python (numpy, scipy, pyproj, matplotlib); MapLibre for the interactive maps.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
for t in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in t.replace("```", "").replace("|---|---|", ""), bad
os.makedirs(os.path.join(ROOT, "reddit"), exist_ok=True)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("readme, licence, post ok")
