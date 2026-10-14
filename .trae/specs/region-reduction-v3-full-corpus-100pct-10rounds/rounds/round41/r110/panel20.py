"""panel20.py — regenerate + judge the 20-file panel with the MIRROR pipeline.

usage: python -X utf8 panel20.py <tag> <start> <count>
  tag    : output prefix, e.g. cand / base
Products go to D:/Temp/r108/out/panel_<tag>_<name>.py, verdicts appended to
D:/Temp/r108/logs/panel_<tag>.txt.  Paths in PANEL list are repo-relative -> joined with ROOT.
"""
import os
import subprocess
import sys

MIRROR = r'D:/Temp/r108'
ROOT = r'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'
PANEL = os.path.join(ROOT, '.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round38/PANEL_20files.txt')
PY = sys.executable

tag = sys.argv[1]
start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
count = int(sys.argv[3]) if len(sys.argv) > 3 else 99
rel = [l.strip() for l in open(PANEL, encoding='utf-8-sig') if l.strip()]

out_dir = os.path.join(MIRROR, 'out')
log = os.path.join(MIRROR, 'logs', 'panel_%s.txt' % tag)
os.makedirs(os.path.join(MIRROR, 'logs'), exist_ok=True)
fh = open(log, 'a', encoding='utf-8')
for i in range(start, min(start + count, len(rel))):
    r = rel[i]
    pyc = os.path.join(ROOT, 'site-packages', r)
    name = os.path.splitext(os.path.basename(r))[0] + '__' + os.path.basename(os.path.dirname(r))
    pr = os.path.join(out_dir, 'panel_%s_%d_%s.py' % (tag, i, name))
    if not os.path.isfile(pyc):
        line = '[panel %s #%d] NOPYC %s' % (tag, i, r)
        print(line, flush=True); fh.write(line + '\n'); continue
    try:
        d = subprocess.run([PY, '-X', 'utf8', os.path.join(MIRROR, 'pycdc.py'), pyc, '-o', pr],
                           cwd=MIRROR, capture_output=True, timeout=240)
    except Exception as e:
        line = '[panel %s #%d] DECOMP_TIMEOUT %s %r' % (tag, i, r, e)
        print(line, flush=True); fh.write(line + '\n'); continue
    sz = os.path.getsize(pr) if os.path.isfile(pr) else -1
    if d.returncode != 0 or sz < 100:
        line = '[panel %s #%d] DECOMP_FAIL rc=%s size=%d %s' % (tag, i, d.returncode, sz, (d.stderr or '')[-150:])
        print(line, flush=True); fh.write(line + '\n'); continue
    try:
        v = subprocess.run([PY, '-X', 'utf8', os.path.join(ROOT, 'scripts/pyc_verify.py'), 'single', pyc,
                            '--source', pr], cwd=ROOT, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=240)
    except Exception as e:
        line = '[panel %s #%d] JUDGE_TIMEOUT %s %r' % (tag, i, r, e)
        print(line, flush=True); fh.write(line + '\n'); continue
    txt = (v.stdout or '') + (v.stderr or '')
    verdict = [l.strip() for l in txt.splitlines() if 'status=' in l]
    fails = [l.strip()[:110] for l in txt.splitlines() if l.strip().startswith('***')]
    line = '[panel %s #%d] %-60s size=%-8d %s  failing=%d' % (
        tag, i, r, sz, verdict[-1] if verdict else 'NO_VERDICT', len(fails))
    print(line, flush=True)
    fh.write(line + '\n')
    for f in fails[:6]:
        print('      ' + f, flush=True)
        fh.write('      ' + f + '\n')
fh.close()
print('[panel %s] shard %d+%d done' % (tag, start, count), flush=True)
