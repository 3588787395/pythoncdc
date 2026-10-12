"""Regenerate all 20 panel files from the CURRENT mirror bytes (no judge) into out/<tag>/,
so two byte-builds can be compared file-by-file (byte-change census).

usage: python -X utf8 work/regen_only.py <tag> <lo> <hi>
"""
import os
import subprocess
import sys

ROOT = 'D:/Temp/r76'
SPEC = ('D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/.trae/specs/'
        'region-reduction-v3-full-corpus-100pct-10rounds')
SP = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages'
TAG, LO, HI = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
FILES = [l.strip() for l in open(os.path.join(SPEC, 'rounds/round38/PANEL_20files.txt'),
                                 encoding='utf-8') if l.strip()]
OUT = os.path.join(ROOT, 'out', TAG)
os.makedirs(OUT, exist_ok=True)
for idx, rel in enumerate(FILES, 1):
    if not (LO <= idx <= HI):
        continue
    prod = os.path.join(OUT, rel.replace('/', '__').replace('.pyc', 'OK.py'))
    if os.path.exists(prod):
        os.remove(prod)
    r = subprocess.run([sys.executable, '-X', 'utf8', 'pycdc.py', '--region', '-o', prod,
                        os.path.join(SP, rel)], cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', env=dict(os.environ))
    print('%2d %-70s rc=%s size=%s' % (idx, rel, r.returncode,
                                       os.path.getsize(prod) if os.path.exists(prod) else 'FAIL'),
          flush=True)
