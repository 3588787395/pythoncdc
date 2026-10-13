"""Install a certified candidate pair into the repo, then launch the round gate.

Refuses to install unless:
  * the target file's JUDGE units line reads n/n (100%), which is the only authority, and
  * the mandatory 402-product collateral sweep is supplied and reads bad=0 with changed>=1.
  A non-zero GOLD-diff hunk count no longer blocks an install: the expressibility probe
  rounds/round40/r100/PROBE_source_flat_chain_in_place.py measured a flattened reconnect chain
  in the right position judging status=success units=128/128, so "diff against GOLD is empty" is
  a SUFFICIENT but NOT NECESSARY condition (ticket addendum 23).
  * both files are BOM + all-CRLF with zero CR-CR-LF and py_compile clean,
  * `git status --porcelain -- core/` afterwards lists EXACTLY the two core files.

usage: python -X utf8 install_pair.py --ana <analyzer> --gen <generator> --gold-hunks N --units "x/y"
       (dry run without --commit-notice; the gate is launched only with --gate)
"""
import argparse
import re
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
ap.add_argument("--sweep", default="")
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
print("[gold-diff hunks] %d  (informational only - sufficient, not necessary)" % A.gold_hunks)
m = re.match(r"^\s*(\d+)/(\d+)\s*$", A.units or "")
if not m:
    print('REFUSING: --units must be the judge line "n/n", got %r' % (A.units,))
    sys.exit(1)
n, d = int(m.group(1)), int(m.group(2))
if n != d or d == 0:
    print("REFUSING: judge units %s is NOT 100%% of the target file - bank it instead of installing" % A.units)
    sys.exit(1)
print("[judge units] %s == 100%% of the target file" % A.units)
sm = re.search(r"ok=(\d+)\s+bad=(\d+)\s+changed=(\d+)", A.sweep or "")
if not sm:
    print('REFUSING: --sweep "ok=402 bad=0 changed=N" (the 402-product CR-stripped sweep) is required')
    sys.exit(1)
if int(sm.group(2)) != 0 or int(sm.group(3)) < 1:
    print("REFUSING: sweep reads ok=%s bad=%s changed=%s" % sm.groups())
    sys.exit(1)
print("[sweep] ok=%s bad=%s changed=%s" % sm.groups())

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
