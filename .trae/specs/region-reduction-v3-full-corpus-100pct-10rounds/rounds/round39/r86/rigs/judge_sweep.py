"""Judge swept products (mirrored directory layout) for an explicit list of roster rel paths.

usage: python -X utf8 work/judge_sweep.py <sweepdir> <rel1> [rel2 ...]
"""
import os
import re
import subprocess
import sys

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
SW = sys.argv[1]
rels = sys.argv[2:]
pat = re.compile(r'units=(\d+)/(\d+)')
for rel in rels:
    pyc = os.path.join(REPO, rel.replace('/', os.sep))
    prod = os.path.normpath(os.path.join(SW, rel[:-4] + '.py'))
    if not os.path.isfile(prod):
        print('%-62s NO SWEPT PRODUCT' % rel)
        continue
    r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(MIRROR, 'scripts', 'pyc_verify.py'),
                        'single', pyc, '--source', prod], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    out = (r.stdout or '') + (r.stderr or '')
    m = pat.search(out)
    print('%-62s %s' % (rel, 'units=%s/%s' % m.groups() if m else 'NO-UNITS rc=%s' % r.returncode))
    for l in out.splitlines():
        if l.strip().startswith('***'):
            print('    FAIL ' + l.strip()[:140])
