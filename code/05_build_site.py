"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, japan.json, world.json) is embedded; the sheet images are in img/.
Facts stated in words are checked here. The full-screen map snippet (code/fullscreen_snippet.html) is pasted before
</body>. 10.5281/zenodo.23882609, https://doi.org/10.5281/zenodo.23882609 and https://blog.tristanhotham.com/2026/10/31/ino-japan/ stay as placeholders for the publisher."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
KEEP = {"DOI", "BLOG_URL", "DOI_URL"}
C, Q, D, N = R["coast"], R["fitq"], R["distortion"], R["national"]

# facts stated in words (page, blog, paper, collage)
assert C["median_of_sheets_m"] < 500 and C["within1000_median_pct"] >= 85              # "within a few hundred metres", "a kilometre"
assert R["expect"]["coast_x_draw"] >= 10                                                 # gap well above drafting error
assert Q["aff_loo_median_m"] >= Q["sim_loo_on_aff_sheets_m"]                             # "does no better"
assert Q["quad_loo_m"] > Q["aff_loo_on_quad_sheets_m"]                                    # "does worse"
assert R["ctrl"]["n"] < R["ctrl"]["target"]                                              # "well short of"
assert abs(N["rms_ew_km"] - N["rms_ns_km"]) < 1.5                                        # "the same size"
assert N["ci_lo_pct"] > 0                                                                # stretch interval excludes zero
assert R["ctrl"]["named"]["Cape Erimo"]["res_m"] == R["ctrl"]["max_m"]                   # "the largest is Cape Erimo"
assert all(v["sheets"] > 0 for v in R["regions"].values())
assert R["source"]["drafts"] + 4 == R["source"]["not_located"]                           # drafts plus four blank or slight sheets


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{(?!DOI\}\}|BLOG_URL\}\}|DOI_URL\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    left = set(re.findall(r"\{\{([^}]*)\}\}", html))
    assert left <= KEEP, left
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*JAPAN*/", open(f"{DATA}/japan.json", encoding="utf-8").read()).replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
