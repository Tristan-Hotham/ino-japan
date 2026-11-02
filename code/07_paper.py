"""Build the paper: fill code/paper_template.tex from data/results.json, add the sheet table, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays as the 10.5281/zenodo.23882609 placeholder."""
import subprocess
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Ino_Japan"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
assert R["ctrl"]["max_m"] == R["ctrl"]["named"]["Cape Erimo"]["res_m"]
assert abs(R["national"]["slope_ew"]) < 1 and abs(R["national"]["slope_ns"]) < 1          # "neither component trends with longitude"
assert R["distortion"]["rot_abs_median"] < 2                                                # "within about a degree or two"


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


S = pd.read_csv(f"{DATA}/sheet_summary.csv").set_index("sheet")
IDX = pd.read_csv(f"{DATA}/sheet_index.csv")
rows = ""
for r in IDX.itertuples():
    if r.status == "located":
        s = S.loc[r.sheet]
        ctrl = f"{int(s.n_ctrl)} & {int(s.ctrl_rigid_median_m):,}" if s.n_ctrl > 0 else "0 & "
        rows += f"{r.sheet} & {tex(r.place)} & {tex(r.region)} & {int(s.coast_km)} & {int(s.coast_median_m)} & {s.coast_within_500_pct:.0f} & {s.rotation_deg:.1f} & {ctrl}\\\\\n"
    else:
        rows += f"{r.sheet} & \\multicolumn{{8}}{{l}}{{\\textit{{not placed: {tex(r.note)}}}}}\\\\\n"
TS = ("{\\footnotesize\\setlength{\\tabcolsep}{4pt}\\begin{longtable}{rp{4.2cm}p{2.6cm}rrrrrr}\\caption{The " + str(len(IDX)) + " sheets: area, region, length of drawn coast measured (km), median gap to the modern coast (m), share within 500 m (\\%), rotation from true north (degrees, anticlockwise positive), number of control points and their median error (m).}\\label{tab:sheets}\\\\"
      "\\toprule Sheet & Area & Region & km & Gap & 500 m & Rot. & Pts & Error\\\\\\midrule\\endfirsthead\\toprule Sheet & Area & Region & km & Gap & 500 m & Rot. & Pts & Error\\\\\\midrule\\endhead\n" + rows + "\\bottomrule\\end{longtable}}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_|meta\.doi)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
t = t.replace("{{TABLE_SHEETS}}", TS)
t = t.replace("\\href{https://doi.org/{{meta.doi}}}{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(3):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
