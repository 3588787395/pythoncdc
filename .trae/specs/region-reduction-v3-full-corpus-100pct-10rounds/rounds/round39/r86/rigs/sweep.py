"""Collateral sweep: regenerate EVERY roster product from the mirror's current bytes into a
mirrored directory (so same-basename files do not collide).

usage: python -X utf8 work/sweep.py <budget_sec> <pathlist> <outdir> [start]
prints NEXT=<cursor> and exits rc=3 when the budget is hit.
"""
import os
import subprocess
import sys
import time

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"

budget = float(sys.argv[1])
paths = [l.strip() for l in open(sys.argv[2], encoding='utf-8') if l.strip()]
outdir = sys.argv[3]
start = int(sys.argv[4]) if len(sys.argv) > 4 else 0
t0 = time.time()
ok = bad = 0
bad_list = []
cursor = start
for cursor in range(start, len(paths)):
    if time.time() - t0 > budget:
        print('BUDGET NEXT=%d ok=%d bad=%d' % (cursor, ok, bad))
        sys.exit(3)
    rel = paths[cursor]
    pyc = os.path.join(REPO, rel.replace('/', os.sep))
    prod = os.path.join(outdir, rel[:-4] + '.py')
    prod = os.path.normpath(prod)
    if os.path.isfile(prod):
        os.remove(prod)
    if not os.path.isfile(pyc):
        bad += 1
        bad_list.append(rel + ' (no pyc)')
        continue
    os.makedirs(os.path.dirname(prod), exist_ok=True)
    try:
        r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(MIRROR, 'pycdc.py'),
                            '--region', '-o', prod, pyc], cwd=MIRROR,
                           capture_output=True, text=True, encoding='utf-8',
                           errors='replace', timeout=120)
        good = r.returncode == 0 and os.path.isfile(prod)
    except subprocess.TimeoutExpired:
        good = False
    if good:
        ok += 1
    else:
        bad += 1
        bad_list.append(rel)
print('SWEEP done ok=%d bad=%d elapsed=%.0fs' % (ok, bad, time.time() - t0))
for b in bad_list[:20]:
    print('  BAD', b)
