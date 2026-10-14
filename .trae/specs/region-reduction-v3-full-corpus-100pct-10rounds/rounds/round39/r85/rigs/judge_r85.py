"""Judge every product in <outdir> against its panel pyc with scripts/pyc_verify.py single.
Prints the machine line `[single] ... units=X/Y` per file, so base-vs-candidate panels compare
unit counts directly (a decrease is a regression).

usage (from mirror root): python -X utf8 work/judge_r85.py <outdir>
"""
import os
import re
import subprocess
import sys

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
SP = os.path.join(REPO, "site-packages")
OUT = sys.argv[1]

files = [l.strip() for l in open(os.path.join(MIRROR, 'PANEL_20files.txt'), encoding='utf-8') if l.strip()]
seen = set()
uniq = []
for f in files:
    if f not in seen:
        seen.add(f)
        uniq.append(f)

pat = re.compile(r'units=(\d+)/(\d+)')
for rel in uniq:
    pyc = os.path.join(SP, rel.replace('/', os.sep))
    prod = os.path.join(OUT, os.path.splitext(os.path.basename(pyc))[0] + '.py')
    if not os.path.exists(prod):
        print('%-62s NO PRODUCT' % rel)
        continue
    r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(MIRROR, 'scripts', 'pyc_verify.py'),
                        'single', pyc, '--source', prod], capture_output=True, text=True)
    out = (r.stdout or '') + (r.stderr or '')
    m = pat.search(out)
    fails = [l.strip() for l in out.splitlines() if l.strip().startswith('***')]
    print('%-62s %s' % (rel, 'units=%s/%s' % m.groups() if m else 'NO-UNITS-LINE rc=%s' % r.returncode))
    for f in fails:
        print('    FAIL ' + f[:130])
