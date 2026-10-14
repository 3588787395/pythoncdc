"""R21-44 panel regeneration: regenerate all 20 panel files from the mirror with a given
analyzer build, into outdir, printing per-file judge units via pyc_verify single.
Usage: python -X utf8 panel_r71.py <outdir>
"""
import os, sys, subprocess, json, shutil
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
MIRROR = r"D:/Temp/r71"
sys.path.insert(0, MIRROR)
FILES = [l.strip() for l in open(os.path.join(REPO, '.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round38/PANEL_20files.txt')) if l.strip()]
outdir = sys.argv[1]
os.makedirs(outdir, exist_ok=True)
for rel in FILES:
    pyc = os.path.join(REPO, 'site-packages', *rel.split('/'))
    uniq = rel.replace('/', '_').replace('.pyc', '')
    out = os.path.join(outdir, uniq + '_panelOK.py')
    if os.path.exists(out):
        os.remove(out)
    r = subprocess.run([sys.executable, '-X', 'utf8', 'pycdc.py', '--region', '-o', out, pyc],
                       cwd=MIRROR, capture_output=True, text=True)
    print('%-60s rc=%d size=%d' % (rel, r.returncode, os.path.getsize(out) if os.path.exists(out) else -1))
