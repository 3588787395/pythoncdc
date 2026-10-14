"""Regenerate decompiler products for an explicit list of .pyc paths (producer-only).

Usage: python -X utf8 regen_list.py <budget_sec> <pathlist_file> [start]
Writes each X.pyc -> XOK.py in place via pycdc.py. Prints NEXT=<cursor> so the
caller can resume after the budget guard exits with rc=3.
"""
import os
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if not os.path.isfile(os.path.join(ROOT, 'pycdc.py')):
    sys.exit('[fatal] ROOT 解析错误：%s 下没有 pycdc.py' % ROOT)

budget = float(sys.argv[1])
paths = [l.strip() for l in open(sys.argv[2], encoding='utf-8') if l.strip()]
start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
t0 = time.time()
ok = bad = 0
bad_list = []
cursor = start
for cursor in range(start, len(paths)):
    if time.time() - t0 > budget:
        print('BUDGET NEXT=%d ok=%d bad=%d' % (cursor, ok, bad))
        sys.exit(3)
    rel = paths[cursor]
    pyc = os.path.join(ROOT, rel.replace('/', os.sep))
    prod = pyc[:-4] + 'OK.py'
    if not os.path.isfile(pyc):
        bad += 1
        bad_list.append(rel + ' (no pyc)')
        continue
    if os.path.isfile(prod):
        os.remove(prod)
    try:
        r = subprocess.run([sys.executable, 'pycdc.py', '-o', prod, rel], cwd=ROOT,
                           capture_output=True, text=True, encoding='utf-8',
                           errors='replace', timeout=90)
        good = r.returncode == 0 and os.path.isfile(prod)
    except subprocess.TimeoutExpired:
        good = False
    if good:
        ok += 1
    else:
        bad += 1
        bad_list.append(rel)
print('REGEN done ok=%d bad=%d elapsed=%.0fs' % (ok, bad, time.time() - t0))
for b in bad_list[:20]:
    print('  BAD', b)
