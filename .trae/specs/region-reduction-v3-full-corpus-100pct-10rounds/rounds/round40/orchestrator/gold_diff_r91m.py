"""Count how far a product still is from the GOLD text of one unit.

usage: python -X utf8 gold_diff_r91m.py <product.py> [unit]
Exit prints: ours/GOLD line counts and the number of unified-diff hunks (0 == product text IS GOLD).
GOLD = rounds/round40/r91/broker_GOLD_PROOF.py, which I judged status=success units=128/128 on the
trade_live_broker corpus input, so "0 hunks" is a sufficient condition for the unit to be Equal.
"""
import difflib
import os
import sys

REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
GOLD = os.path.join(REPO, ".trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round40/r91/broker_GOLD_PROOF.py")
unit = sys.argv[2] if len(sys.argv) > 2 else "_sync_worker"


def body(path, name):
    L = open(path, encoding="utf-8-sig").read().replace("\r", "").split("\n")
    hits = [i for i, l in enumerate(L) if ("def " + name) in l]
    if not hits:
        return None
    s = hits[0]
    ind = len(L[s]) - len(L[s].lstrip())
    for j in range(s + 1, len(L)):
        l = L[j]
        if l.strip() and (len(l) - len(l.lstrip())) <= ind and l.lstrip().startswith(("def ", "class ", "@")):
            return L[s:j]
    return L[s:]


a, b = body(sys.argv[1], unit), body(GOLD, unit)
if a is None or b is None:
    print("unit %s not found (ours=%s gold=%s)" % (unit, a is not None, b is not None))
    sys.exit(2)
d = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l.startswith("@@")]
print("unit=%s ours=%d lines GOLD=%d lines  hunks_vs_GOLD=%d" % (unit, len(a), len(b), len(d)))
for l in d:
    print("   " + l)
