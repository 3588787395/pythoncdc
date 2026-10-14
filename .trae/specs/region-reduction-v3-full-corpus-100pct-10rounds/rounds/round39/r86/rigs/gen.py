"""Regenerate products for an explicit list of repo-relative .pyc paths using the MIRROR's bytes.

usage: python -X utf8 work/gen.py <outdir> <rel1> [rel2 ...]
Each product is deleted first, then produced with `pycdc.py --region -o <out> <abs pyc>`.
"""
import os
import subprocess
import sys

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
OUT = sys.argv[1]
rels = sys.argv[2:]
os.makedirs(OUT, exist_ok=True)
for rel in rels:
    pyc = os.path.join(REPO, rel.replace('/', os.sep))
    prod = os.path.join(OUT, os.path.splitext(os.path.basename(pyc))[0] + '.py')
    if os.path.exists(prod):
        os.remove(prod)
    r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(MIRROR, 'pycdc.py'),
                        '--region', '-o', prod, pyc], cwd=MIRROR,
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    size = os.path.getsize(prod) if os.path.exists(prod) else -1
    print('GEN rc=%s size=%s %s' % (r.returncode, size, rel))
    if r.returncode != 0:
        print((r.stderr or r.stdout or '')[-400:])
