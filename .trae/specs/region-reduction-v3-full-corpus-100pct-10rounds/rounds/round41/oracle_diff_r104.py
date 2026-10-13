"""One-command adjudication for the last unit: oracle distance + edge census + judge line.

usage: python -X utf8 oracle_diff_r104.py <product.py>

Controls: the 13/13 oracle itself must print hunks_vs_ORACLE=0 / all-equal / units=13/13;
the landed pipeline product must print non-zero on every one of those.
"""
import difflib
import os
import subprocess
import sys

REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
SPEC = ".trae/specs/region-reduction-v3-full-corpus-100pct-10rounds"
ORACLE = os.path.join(REPO, SPEC, "rounds/round41/GOLD_realtime_event_source_PROOF.py")
PYC = os.path.join(
    REPO, "site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc"
)


def body(path, name="clock_worker"):
    text = open(path, encoding="utf-8-sig").read().replace(chr(13), "")
    L = text.split(chr(10))
    hits = [i for i, line in enumerate(L) if ("def " + name) in line]
    if not hits:
        return []
    i = hits[0]
    nxt = [n for n in range(i + 1, len(L)) if L[n].startswith("        def ") or L[n].startswith("    def ")]
    return L[i:(nxt[0] if nxt else min(i + 400, len(L)))]


def run(cmd, cwd, tmo):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=cwd, timeout=tmo)
    return (r.stdout or "") + (r.stderr or "")


def main():
    prod = sys.argv[1]
    a, b = body(prod), body(ORACLE)
    hunks = [l for l in difflib.unified_diff(b, a, "ORACLE", "PRODUCT", lineterm="", n=0)
             if l.startswith("@@")]
    print("[oracle-diff] unit=clock_worker ours=%d ORACLE=%d hunks_vs_ORACLE=%d"
          % (len(a), len(b), len(hunks)))
    for h in hunks[:6]:
        print("   " + h)

    out = run([sys.executable, "-X", "utf8", "-u",
               os.path.join(REPO, SPEC, "rounds/round41/census_diff_r104.py"), prod], REPO, 120)
    for line in out.splitlines():
        if line.startswith(("DELTAS", "indeg-equal")):
            print("[census] " + line)

    out = run([sys.executable, "-X", "utf8", "scripts/pyc_verify.py", "single", PYC,
               "--source", prod], REPO, 180)
    for line in out.splitlines():
        if "clock_worker" in line or "status=" in line:
            print("[judge] " + line.strip())


main()
