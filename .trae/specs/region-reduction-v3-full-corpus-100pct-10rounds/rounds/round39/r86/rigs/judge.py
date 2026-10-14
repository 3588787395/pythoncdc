"""Judge every product in <outdir> against its pyc with the mirror's scripts/pyc_verify.py single.

usage: python -X utf8 work/judge.py <outdir> [rel1 rel2 ...]
Prints `[single] status=... units=X/Y` plus every `***` failing unit line per file.
"""
import os
import re
import subprocess
import sys

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
OUT = sys.argv[1]
rels = sys.argv[2:] or sorted(
    'site-packages/' + os.path.relpath(os.path.join(dp, f), os.path.join(REPO, 'site-packages')).replace(os.sep, '/')
    for dp, _dn, fn in os.walk(os.path.join(REPO, 'site-packages')) for f in fn
    if False)
if not rels:
    # derive from outdir product names is ambiguous; require explicit list
    sys.exit('usage: judge.py <outdir> rel...')
pat = re.compile(r'units=(\d+)/(\d+)')
for rel in rels:
    pyc = os.path.join(REPO, rel.replace('/', os.sep))
    prod = os.path.join(OUT, os.path.splitext(os.path.basename(pyc))[0] + '.py')
    if not os.path.exists(prod):
        print('%-62s NO PRODUCT' % rel)
        continue
    r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(MIRROR, 'scripts', 'pyc_verify.py'),
                        'single', pyc, '--source', prod], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    out = (r.stdout or '') + (r.stderr or '')
    m = pat.search(out)
    status = [l for l in out.splitlines() if 'status=' in l]
    print('%-62s %s' % (rel, 'units=%s/%s' % m.groups() if m else 'NO-UNITS rc=%s' % r.returncode))
    for l in status[-1:]:
        print('    ' + l.strip()[:160])
    for l in out.splitlines():
        if l.strip().startswith('***'):
            print('    FAIL ' + l.strip()[:140])
