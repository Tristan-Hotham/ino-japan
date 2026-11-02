# Ino's Japan: how close did the survey map of 1821 get?

Ino Tadataka's large-scale survey map of Japan (Dai Nihon Enkai Yochi Zenzu, completed 1821) set against a modern map. The 40 sheets of the Library of Congress manuscript copy that are photographed on Wikimedia Commons (sheets 1 to 40, all in the far north at 1:43,600) are placed on the modern coast by matching their drawn coastlines; 28 are located, and their coastlines, control points, rotation and scale are measured. A whole-Japan map of 1878 compiled from the survey gives a national check of latitude and longitude.

Interactive page: https://maps.tristanhotham.com/ino-japan/
Paper: https://doi.org/10.5281/zenodo.23882609
Blog post: https://blog.tristanhotham.com/2026/10/31/ino-japan/

## Headline results

- Coverage: 40 of 214 sheets (18.7%), all Hokkaido, the southern Kurils and Sakhalin; 28 placed, 8 unfinished pencil drafts and 4 others too slight to place.
- Coastline: after one shift and one rotation per sheet at the nominal scale, the drawn coast of a typical sheet is a median 280 m from Natural Earth's 1:10m coast (6.4 mm on the paper); 69% within 500 m and 90% within 1 km; 1,494 km of drawn coast measured. Best sheet 26 (Hidaka-Monbetsu, 108 m), worst 25 (Shizunai, 651 m).
- Control points: 93 (23 picked by eye, 70 automatic coast windows) on 16 sheets, a median 543 m from their true positions; 72% within 1 km. Fewer than the 250 aimed for.
- Fits: similarity leave-one-out median 508 m on 10 sheets; affine 536 m against 536 m on 6 sheets; quadratic 824 m against 448 m on 2 sheets. No sign of distortion within sheets beyond shift, rotation and scale.
- Rotation and scale: median absolute rotation from true north 1.3 degrees on 15 sheets whose coast fixes the angle; scales 0.951 to 1.034 of nominal on 6 well-controlled sheets.
- National (1878 map): 18 capes and islands a median 7.9 km from a best-fitting modern position; root mean square error 6.2 km north-south and 7.1 km east-west; east-west scale 1.9% longer than north-south (95% interval 0.1 to 3.8%).
- All distances are upper bounds on survey error: they include copying, paper distortion, picking and the generalisation of the modern coast.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/05_build_site.py`; page data embedded; sheet images in `img/`). |
| `header.png` | Social card, 1200 x 630. |
| `img/sheet_N.jpg` | The 40 sheets, 1,600 px on the long side (Library of Congress, public domain). `img/whole1878.jpg` the 1878 map; `img/replica.jpg` a photograph of a full-size replica. |
| `data/sheet_index.csv` | Hand-checked table of all 40 sheets: placed or not, region, area, starting position and rotation for the fit, reason when not placed (input). |
| `data/control_points.csv` | The 23 control points I picked by eye: sheet pixel, modern position on Natural Earth's coast, confidence (input). |
| `data/national_points.csv` | The 18 features picked on the 1878 map with modern positions (input). |
| `data/sheets.json` | Every sheet's extracted coast (sheet pixels, one point per 8 px cell) and its rigid coastline fit. |
| `data/fits.json` | Per-sheet fits and measures, image corners for the web map, national fit. |
| `data/control_fit.csv` | All 93 control points with their errors. |
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
- Control points: capes picked by eye, and coast windows 8 km across matched by local translation where the coast curves enough; errors against the coastline fit, which does not use them; similarity, affine and quadratic fits with leave-one-out errors.
- National: similarity and affine fits of 18 picked points on the 1878 map; north-south and east-west residuals; bootstrap of the scale ratio.
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

- Ino Tadataka and team, Dai Nihon Enkai Yochi Zenzu, large-scale sheets 1 to 40, manuscript copy, Library of Congress Geography and Map Division, item 2001620020 (https://www.loc.gov/item/2001620020/). Public domain; photographs via Wikimedia Commons ("Dai Nihon enkai yochi zenzu LOC 2001620020-N.jpg").
- Dai Nihon Zenzu, Army General Staff Bureau, 1878, Wikimedia Commons, public domain.
- Replica photograph: Wikimedia Commons, "Inoh taizu 01.jpg" (https://commons.wikimedia.org/wiki/File:Inoh_taizu_01.jpg).
- Natural Earth 1:10m and 1:50m countries (public domain). Optional relief tiles on the page: Esri.

## Citation

Hotham, T. (2026) Ino's Japan: how close did the survey map of 1821 get? Zenodo. https://doi.org/10.5281/zenodo.23882609

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
