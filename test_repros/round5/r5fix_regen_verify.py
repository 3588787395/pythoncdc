# -*- coding: utf-8 -*-
"""探针：对给定 pyc 逐个 regen + verify（RV2），打印 status。
用法: python test_repros/round5/r5fix_regen_verify.py <pattern-or-dir> [names...]
"""
import os, sys, subprocess, glob

ROOT = r'f:\Downloads\pythoncdc-main'
D = os.path.dirname(os.path.abspath(__file__))

def regen_verify(pyc):
    if not os.path.isfile(pyc):
        return pyc, 'MISSING', ''
    src = pyc[:-4] + 'OK.py'
    subprocess.run([sys.executable, os.path.join(ROOT, 'pycdc.py'), pyc, '-o', src],
                   capture_output=True, text=True)
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                        'single', pyc], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    out = (r.stdout or '') + (r.stderr or '')
    status = 'FAIL'
    for line in out.splitlines():
        if 'status=' in line:
            status = line.split('status=')[1].split()[0]
    fails = [l.strip() for l in out.splitlines() if 'Failure' in l]
    return pyc, status, '; '.join(fails)

targets = []
args = sys.argv[1:]
if args and os.path.isdir(args[0]):
    d = args[0]
    for n in args[1:]:
        targets.append(os.path.join(d, n + '.pyc'))
    if not args[1:]:
        targets = sorted(glob.glob(os.path.join(d, '*.pyc')))
else:
    for a in args:
        targets.append(a)

for pyc in targets:
    p, st, fl = regen_verify(pyc)
    print('%-9s %s %s' % (st, os.path.basename(p), fl[:90]))