"""Panel byte-change census: generate each of the 20 panel pyc files with the INSTALLED mirror
bytes and print product sha16 + byte length. Run once with landed bytes, once with the candidate;
compare to get `changed files = N`.

usage (from mirror root): python -X utf8 work/panel_r85.py <outdir>
"""
import hashlib
import os
import subprocess
import sys

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
SP = os.path.join(REPO, "site-packages")
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

files = [l.strip() for l in open(os.path.join(MIRROR, 'PANEL_20files.txt'), encoding='utf-8') if l.strip()]
seen = set()
uniq = []
for f in files:
    if f not in seen:
        seen.add(f)
        uniq.append(f)

for rel in uniq:
    pyc = os.path.join(SP, rel.replace('/', os.sep))
    base = os.path.splitext(os.path.basename(pyc))[0]
    outp = os.path.join(OUT, base + '.py')
    if os.path.exists(outp):
        os.remove(outp)
    r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(MIRROR, 'pycdc.py'),
                        '--region', '-o', outp, pyc], capture_output=True, text=True)
    if not os.path.exists(outp):
        print('%-62s ERR rc=%s %s' % (rel, r.returncode, (r.stderr or '')[:80]))
        continue
    d = open(outp, 'rb').read()
    print('%-62s sha16=%s bytes=%d' % (rel, hashlib.sha256(d).hexdigest()[:16], len(d)))
