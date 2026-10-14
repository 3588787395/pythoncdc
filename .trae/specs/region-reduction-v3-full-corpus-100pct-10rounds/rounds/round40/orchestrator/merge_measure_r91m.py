"""Merge several engineer generator candidates onto the landed bytes, install, regenerate, judge.

Why this exists: round 40 splits one unit across several mirrors, each candidate built on a
different base (landed bytes, or the banked analyzer candidate). Installing any one whole file
silently reverts the others, so candidates are transplanted hunk-by-hunk onto a moving base with
`merge_hunks.py` (content-anchored, self-proving) and only the merged result is measured.

usage:
  python -X utf8 merge_measure_r91m.py \
      --pair BASE_FILE CANDIDATE_FILE [--pair ...]   # apply order = left to right
      [--analyzer ANALYZER_FILE]                     # omit to keep the landed analyzer
      [--files NAME=ABS_PYC ...]                     # panel to regen+judge; NAME is a label

Every merge step re-diffs merged-vs-candidate and prints the residual count; a residual that is not
explained by the skip marker means the transplant was not faithful, and the run stops.
"""
import argparse
import os
import subprocess
import sys

REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
MIRROR = r"D:/Temp/r91m"
MERGE = os.path.join(REPO, ".trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/merge_hunks.py")
GEN = os.path.join("core", "cfg", "region_ast_generator.py")
ANA = os.path.join("core", "cfg", "region_analyzer.py")

ap = argparse.ArgumentParser()
ap.add_argument("--pair", action="append", default=[], nargs=2)
ap.add_argument("--analyzer", default="")
ap.add_argument("--file", action="append", default=[])
ap.add_argument("--skip-merge", action="store_true")
A = ap.parse_args()

panel = []
for spec in A.file:
    name, path = spec.split("=", 1)
    panel.append((name, path))


def sha16(p):
    import hashlib
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def run(cmd):
    r = subprocess.run([sys.executable, "-X", "utf8"] + cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=280)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


work = os.path.join(MIRROR, "merge")
os.makedirs(work, exist_ok=True)
cur = os.path.join(REPO, GEN)
print("[merge] landed generator = %s" % sha16(cur))

if not A.skip_merge:
    for i, (base, cand) in enumerate(A.pair, 1):
        out = os.path.join(work, "merged_%d_%s.py" % (i, sha16(cand)))
        rc, log = run([MERGE, "--base", base, "--candidate", cand, "--current", cur, "--out", out])
        tail = [l for l in log.splitlines() if l.strip()][-6:]
        print("[merge %d] cand=%s base=%s rc=%d" % (i, sha16(cand), sha16(base), rc))
        for l in tail:
            print("    | " + l[:150])
        if rc != 0 or not os.path.exists(out):
            print("[merge %d] FAILED - stopping" % i)
            sys.exit(1)
        cur = out

gen_final = os.path.join(work, "final_gen_%s.py" % sha16(cur))
data = open(cur, "rb").read()
assert data.count(b"\r\r\n") == 0, "merged generator has \\r\\r\\n"
open(gen_final, "wb").write(data)
rc, log = run(["-c", "pass"])  # no-op keeps `rc` defined
import py_compile
try:
    py_compile.compile(gen_final, doraise=True)
    print("[final gen] %s py_compile OK  bytes=%d" % (sha16(gen_final), len(data)))
except Exception as e:
    print("[final gen] py_compile FAILED: %s" % e)
    sys.exit(1)

os.makedirs(os.path.join(MIRROR, "out"), exist_ok=True)
subprocess.run(["cp", gen_final, os.path.join(MIRROR, GEN)], check=False, shell=True) if False else None
import shutil
shutil.copyfile(gen_final, os.path.join(MIRROR, GEN))
if A.analyzer:
    shutil.copyfile(A.analyzer, os.path.join(MIRROR, ANA))
    print("[analyzer] installed %s" % sha16(A.analyzer))
pyc_dir = os.path.join(MIRROR, "core", "cfg", "__pycache__")
if os.path.isdir(pyc_dir):
    shutil.rmtree(pyc_dir)
print("[mirror] gen=%s ana=%s" % (sha16(os.path.join(MIRROR, GEN)), sha16(os.path.join(MIRROR, ANA))))

for name, path in panel:
    prod = os.path.join(MIRROR, "out", "%s.py" % name)
    rc, log = run([os.path.join(MIRROR, "pycdc.py"), path, "-o", prod])
    if rc != 0 or not os.path.exists(prod) or os.path.getsize(prod) < 200:
        print("[regen %s] rc=%d size=%s  <-- BROKEN PRODUCER" % (
            name, rc, os.path.getsize(prod) if os.path.exists(prod) else "missing"))
        continue
    rc2, log2 = run([os.path.join(REPO, "scripts", "pyc_verify.py"), "single", path, "--source", prod])
    verdict = [l for l in log2.splitlines() if "status=" in l or "Failure" in l]
    print("[judge %s] prod=%d" % (name, len(open(prod, "rb").read())))
    for l in verdict[-4:]:
        print("    " + l[:150])
