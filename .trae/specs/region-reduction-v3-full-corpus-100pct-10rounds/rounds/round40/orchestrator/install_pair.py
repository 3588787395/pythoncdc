"""Install a certified candidate pair into the repo, then launch the round gate.

Refuses to install unless:
  * the target unit's judge line and gold-diff hunk count are passed in and consistent,
  * both files are BOM + all-CRLF with zero CR-CR-LF and py_compile clean,
  * `git status --porcelain -- core/` afterwards lists EXACTLY the two core files.

usage: python -X utf8 install_pair.py --ana <analyzer> --gen <generator> --gold-hunks N --units "x/y"
       (dry run without --commit-notice; the gate is launched only with --gate)
"""
import argparse
import os
import subprocess
import sys

REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
SPEC = ".trae/specs/region-reduction-v3-full-corpus-100pct-10rounds"
ap = argparse.ArgumentParser()
ap.add_argument("--ana", required=True)
ap.add_argument("--gen", required=True)
ap.add_argument("--gold-hunks", type=int, required=True)
ap.add_argument("--units", default="")
ap.add_argument("--gate", action="store_true")
A = ap.parse_args()


def sha16(p):
    import hashlib
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def check(p):
    b = open(p, "rb").read()
    bom = b.startswith(b"\xef\xbb\xbf")
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n") - crlf
    crcr = b.count(b"\r\r\n")
    print("  %s sha16=%s BOM=%s CRLF=%d LF=%d CRCRCR=%d bytes=%d" % (os.path.basename(p), sha16(p), bom, crlf, lf, crcr, len(b)))
    assert bom, "missing UTF-8 BOM"
    assert lf == 0, "mixed newline: %d bare LF in a CRLF file" % lf
    assert crcr == 0, "file contains \\r\\r\\n (would break Python parsing)"
    import py_compile
    py_compile.compile(p, doraise=True)


print("[check candidates]")
check(A.ana)
check(A.gen)
if A.gold_hunks != 0:
    print("REFUSING: gold_diff still reports %d hunks - not a flip, bank it instead of installing" % A.gold_hunks)
    sys.exit(1)
print("[candidate units line] %s" % (A.units or "NOT SUPPLIED - refuse"))
if not A.units:
    sys.exit(1)

dsts = [(A.ana, os.path.join(REPO, "core/cfg/region_analyzer.py")),
        (A.gen, os.path.join(REPO, "core/cfg/region_ast_generator.py"))]
for src, dst in dsts:
    data = open(src, "rb").read()
    open(dst, "wb").write(data)
print("[installed] reverifying in place")
for _, dst in dsts:
    check(dst)

st = subprocess.run(["git", "-C", REPO, "status", "--porcelain", "--", "core/"], capture_output=True, text=True)
rows = [l for l in (st.stdout or "").splitlines() if l.strip()]
print("[git status core/] %d line(s)" % len(rows))
for l in rows:
    print("   " + l)
if len(rows) != 2:
    print("REFUSING: expected exactly 2 modified core files")
    sys.exit(1)
ok = subprocess.run(["git", "-C", REPO, "status", "--porcelain", "--", "site-packages/"], capture_output=True, text=True)
prod_dirty = [l for l in (ok.stdout or "").splitlines() if "OK.py" in l]
print("[products dirty] %d (must be 0 before the gate)" % len(prod_dirty))

if A.gate:
    cmd = [sys.executable, "-X", "utf8", "-u", os.path.join(REPO, SPEC, "gate_chain.py"), "40", "39"]
    log = r"D:/Temp/gate40.log"
    print("[gate] %s  -> %s" % (" ".join(cmd), log))
    with open(log, "wb") as fh:
        subprocess.Popen(cmd, cwd=REPO, stdout=fh, stderr=subprocess.STDOUT)
else:
    print("[gate] not launched (pass --gate)")
