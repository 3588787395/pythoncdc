"""Single-half ablation: R21-43 (generator) WITHOUT the R21-40 analyzer half.

The round-38 landing was installed as a pair, so FIX_R21-43_r69a.md 6 records that half-ownership
was never measured. This script removes exactly the [R21-40] lines from the r69 mirror's
region_analyzer.py, proves the removal is correct by the resulting file hash equaling the gate-37
analyzer hash, regenerates trade_live_broker, judges it, and restores the mirror byte-exactly.

Nothing in the repo is touched; the mirror is r69a's own scratch tree.
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys

MIRROR = r"D:/Temp/r69"
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
REL = os.path.join("IQEngine", "plugins", "plugin_system_trade", "trade_live_broker.pyc")
PYC = os.path.join(REPO, "site-packages", REL)
ANA = os.path.join(MIRROR, "core", "cfg", "region_analyzer.py")
OUT = r"D:/Temp/ABL_NO_R40_OK.py"
GATE37_ANALYZER = "c069d359cbfe76b0"
LANDED_ANALYZER = "f7d849e974904492"


def h16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def added_lines():
    """The exact '+' lines of ac41a928's region_analyzer.py hunk, CR-normalized."""
    txt = subprocess.run(["git", "-C", REPO, "show", "ac41a928", "--", "core/cfg/region_analyzer.py"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    out, in_file = [], False
    for ln in txt.split("\n"):
        if ln.startswith("+++"):
            in_file = True
            continue
        if not in_file:
            continue
        if ln.startswith("+"):
            out.append(ln[1:].rstrip("\r"))
    return out


def main():
    orig = open(ANA, "rb").read()
    assert h16(ANA) == LANDED_ANALYZER, "mirror analyzer is not the landed bytes: %s" % h16(ANA)
    shutil.copy2(ANA, ANA + ".r40bak")
    assert open(ANA + ".r40bak", "rb").read() == orig
    try:
        want = added_lines()
        assert want and all(l.strip() for l in want if l.strip()), "empty added-line list"
        nl = b"\r\n" if b"\r\n" in orig else b"\n"
        print("[ablation] mirror analyzer newline = %r" % nl)
        raw = orig.split(nl)
        norm = [x.decode("utf-8", "replace").rstrip(chr(13)) for x in raw]
        # locate the contiguous run of lines equal to the patch's added lines
        idx, found = None, None
        for start in range(len(norm) - len(want) + 1):
            if norm[start:start + len(want)] == want:
                idx = start
                found = norm[start:start + len(want)]
                break
        if idx is None:
            # tolerate one leading blank inside the hunk
            for pad in range(1, 4):
                w = [""] * pad + want
                for start in range(len(norm) - len(w) + 1):
                    if norm[start:start + len(w)] == w:
                        idx, found = start, w
                        break
                if idx is not None:
                    break
        assert idx is not None, "added-line run not found in mirror analyzer (want %d lines)" % len(want)
        removed = raw[idx:idx + len(found)]
        rest = raw[:idx] + raw[idx + len(found):]
        open(ANA, "wb").write(nl.join(rest))
        got = h16(ANA)
        print("[ablation] removed %d lines starting at file line %d" % (len(found), idx + 1))
        print("[ablation] mirror analyzer now %s  (gate-37 expected %s)  MATCH=%s"
              % (got, GATE37_ANALYZER, got == GATE37_ANALYZER))
        if got != GATE37_ANALYZER:
            print("[ablation] ABORT: removal is not exactly the R21-40 block")
            return 2
        if os.path.exists(OUT):
            os.remove(OUT)
        r = subprocess.run([sys.executable, "-X", "utf8", "pycdc.py", "--region", "-o", OUT, PYC],
                           cwd=MIRROR, capture_output=True, text=True, encoding="utf-8", errors="replace")
        size = os.path.getsize(OUT) if os.path.exists(OUT) else 0
        print("[ablation] pycdc rc=%s product=%d bytes" % (r.returncode, size))
        if size < 1000:
            print((r.stderr or "")[-800:])
            return 3
        j = subprocess.run([sys.executable, "-X", "utf8", "scripts/pyc_verify.py", "single", REL,
                            "--source", OUT], cwd=REPO, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        tail = [x for x in (j.stdout or "").splitlines() if x.strip()]
        print("[judge] rc=%s" % j.returncode)
        for x in tail[-14:]:
            print("   " + x)
        print("[judge-cancel-order-lines]")
        for x in tail:
            if "_process_cancel_order" in x or "ipo_stocks_order" in x or "_trade_status_handle" in x:
                print("   " + x.strip()[:200])
        return 0
    finally:
        back = open(ANA + ".r40bak", "rb").read()
        open(ANA, "wb").write(back)
        ok = open(ANA, "rb").read() == orig and h16(ANA) == LANDED_ANALYZER
        print("[restore] mirror analyzer byte-exact = %s (hash %s)" % (ok, h16(ANA)))
        os.remove(ANA + ".r40bak")
        assert ok, "MIRROR NOT RESTORED"


if __name__ == "__main__":
    sys.exit(main())
