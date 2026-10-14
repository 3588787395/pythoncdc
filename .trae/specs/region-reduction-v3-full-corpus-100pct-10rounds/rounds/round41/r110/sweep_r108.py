# -*- coding: utf-8 -*-
"""sweep_r93.py — regenerate all 402 corpus products with the candidate analyzer and
CR-stripped byte-compare each against its committed product (<name>OK.py, also CR-stripped).
Print CHANGED = files whose product differs. Usage: python -X utf8 sweep_r93.py <start> [count]"""
import os, sys, subprocess
MIRROR = 'D:/Temp/r108'
ROOT = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'
_CL='D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round40/r95/corpus402.txt'
paths = [os.path.join(ROOT, l.strip()) for l in open(_CL, encoding='utf-8') if l.strip()]
start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
count = int(sys.argv[2]) if len(sys.argv) > 2 else len(paths)
changed = []
missing = []
for i in range(start, min(start + count, len(paths))):
    p = paths[i]
    if not os.path.isfile(p):
        missing.append(p); continue
    base = p[:-4]  # strip .pyc
    # committed product candidates
    okpy = base + 'OK.py'
    if not os.path.isfile(okpy):
        okpy2 = base + '.py'
        okpy = okpy2 if os.path.isfile(okpy2) else None
    if okpy is None:
        missing.append('NOOK:' + p); continue
    try:
        out = subprocess.run([sys.executable, '-X', 'utf8', MIRROR + '/pycdc.py', p],
                             capture_output=True, cwd=MIRROR, timeout=120)
        prod = out.stdout
    except Exception as e:
        missing.append('DECOMP_FAIL:' + p + ' ' + str(e)); continue
    cand = prod.replace(b'\r\n', b'\n')
    committed = open(okpy, 'rb').read().replace(b'\r\n', b'\n')
    if cand != committed:
        changed.append(os.path.relpath(p, ROOT))
    print('OK %s (idx %d)' % (os.path.relpath(p, ROOT), i))
print('=== SUMMARY ===')
print('files_compared', min(start + count, len(paths)) - start)
print('MISSING/FAIL', len(missing))
for m in missing: print('  MISS', m)
print('CHANGED_COUNT', len(changed))
for c in changed: print('  CHANGED', c)
