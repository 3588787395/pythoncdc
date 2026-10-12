"""Panel byte-change census: for each of the 20 panel pyc files, generate the product with the
INSTALLED generator and print the product sha256[:16] + byte length. Run once with base installed,
once with candidate installed; compare to get `changed files = N`.

usage (from mirror root): python -X utf8 work/panel_products.py <outdir>
"""
import hashlib, os, subprocess, sys

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
SP = os.path.join(REPO, "site-packages")
SPEC = os.path.join(REPO, ".trae", "specs", "region-reduction-v3-full-corpus-100pct-10rounds")
PANEL = os.path.join(SPEC, "rounds", "round38", "PANEL_20files.txt")
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

files = [l.strip().replace("/", os.sep) for l in open(PANEL, encoding="utf-8") if l.strip()]
# dedupe preserving order (panel lists 20 rel paths, some arg_checker/profiler_func are 3 copies)
seen = set(); uniq = []
for f in files:
    if f not in seen:
        seen.add(f); uniq.append(f)

for rel in uniq:
    pyc = os.path.join(SP, rel)
    if not os.path.exists(pyc):
        print("MISSING", rel); continue
    base = os.path.splitext(os.path.basename(pyc))[0]
    outp = os.path.join(OUT, base + ".py")
    if os.path.exists(outp):
        os.remove(outp)
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(MIRROR, "pycdc.py"),
                        "--region", "-o", outp, pyc], capture_output=True, text=True)
    if not os.path.exists(outp):
        print("%-58s ERR rc=%s %s" % (rel, r.returncode, (r.stderr or "")[:80])); continue
    data = open(outp, "rb").read()
    print("%-58s sha16=%s bytes=%d" % (rel, hashlib.sha256(data).hexdigest()[:16], len(data)))
