"""20-file panel regeneration rig (deletes old output first, one pycdc.py subprocess per file).

usage: python -X utf8 panel.py <out-dir>
"""
import os
import subprocess
import sys
import time

MIRROR = 'D:/Temp/r82'
SP = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/'
PANEL = MIRROR + '/PANEL_20files.txt'

out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)
rels = [x.strip() for x in open(PANEL, encoding='utf-8').read().split() if x.strip()]
for rel in rels:
    pyc = os.path.abspath(SP + rel)
    name = rel.replace('/', '_')[:-4] + '.py'
    dst = os.path.join(out_dir, name)
    if os.path.exists(dst):
        os.remove(dst)
    t0 = time.time()
    r = subprocess.run([sys.executable, '-X', 'utf8', MIRROR + '/pycdc.py', '--region',
                        '-o', dst, pyc], capture_output=True, text=True)
    ok = 'OK' if (r.returncode == 0 and os.path.exists(dst)) else 'FAIL rc=%d %s' % (
        r.returncode, (r.stderr or '')[-200:])
    print('%-60s %7.1fs %s %s' % (rel, time.time() - t0, os.path.getsize(dst) if os.path.exists(dst) else 0, ok))
