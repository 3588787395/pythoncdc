# -*- coding: utf-8 -*-
"""sweep_r95.py — regenerate ALL 402 corpus products from the MIRROR bytes into a scratch tree,
then compare CR-stripped against HEAD's committed products (extracted via `git archive HEAD
site-packages | tar -x`). Never writes into the repo.

usage: python -X utf8 sweep_r95.py <budget_sec> <cursor>
Prints one line per file: SAME / CHANGED / NEWPROD / NOPROD / NOINPUT, plus a BUDGET line.
"""
import os
import subprocess
import sys
import time

ROOT = 'D:/Temp/r95'
REPO = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'
OUT = os.path.join(ROOT, 'sp_out')
HEAD = os.path.join(ROOT, 'head_sp')
LIST = os.path.join(ROOT, os.environ.get("SWEEP_LIST","corpus402.txt"))

budget = float(sys.argv[1])
start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
paths = [l.strip() for l in open(LIST, encoding='utf-8') if l.strip()]
os.makedirs(OUT, exist_ok=True)
t0 = time.time()
same = changed = nopro = newp = 0
for cursor in range(start, len(paths)):
    if time.time() - t0 > budget:
        print('BUDGET NEXT=%d same=%d changed=%d newprod=%d nooutput=%d elapsed=%.0fs'
              % (cursor, same, changed, newp, nopro, time.time() - t0))
        sys.stdout.flush()
        sys.exit(3)
    rel = paths[cursor]
    pyc = os.path.join(REPO, rel.replace('/', os.sep))
    prod = os.path.join(OUT, rel[:-4] + 'OK.py')
    ref = os.path.join(HEAD, rel[:-4] + 'OK.py')
    if not os.path.isfile(pyc):
        print('NOINPUT %s' % rel)
        nopro += 1
        continue
    if os.path.isfile(prod):
        os.remove(prod)
    d = os.path.dirname(prod)
    if d:
        os.makedirs(d, exist_ok=True)
    try:
        subprocess.run([sys.executable, '-X', 'utf8', 'pycdc.py', pyc, '-o', prod],
                       cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=180)
    except subprocess.TimeoutExpired:
        print('TIMEOUT %s' % rel)
    if not os.path.isfile(prod) or os.path.getsize(prod) == 0:
        print('NOPROD %s' % rel)
        nopro += 1
        continue
    if not os.path.isfile(ref):
        print('NEWPROD %s' % rel)
        newp += 1
        continue
    a = open(prod, 'rb').read().replace(b'\r\n', b'\n')
    b = open(ref, 'rb').read().replace(b'\r\n', b'\n')
    if a == b:
        same += 1
    else:
        changed += 1
        print('CHANGED %s (%d -> %d bytes)' % (rel, len(b), len(a)))
sys.stdout.flush()
print('DONE files=%d same=%d changed=%d newprod=%d nooutput=%d elapsed=%.0fs'
      % (len(paths), same, changed, newp, nopro, time.time() - t0))
