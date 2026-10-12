"""Install a candidate into the mirror, regenerate realtime_event_source.pyc, print
delta/hunks/landings (unfiltered windows) AND the exact judge line.

usage: python -X utf8 work/vmeasure.py <tag> <candidate-abs-or-rel-path> [pyc-rel]
"""
import os
import shutil
import subprocess
import sys

ROOT = 'D:/Temp/r76'
SP = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages'
REL = sys.argv[3] if len(sys.argv) > 3 else 'IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc'
TAG = sys.argv[1]
CAND = sys.argv[2]
if not os.path.isabs(CAND):
    CAND = os.path.join(ROOT, CAND)

dst = os.path.join(ROOT, 'core', 'cfg', 'region_ast_generator.py')
shutil.copyfile(CAND, dst)
pyc_dir = os.path.join(ROOT, 'core', 'cfg', '__pycache__')
if os.path.isdir(pyc_dir):
    shutil.rmtree(pyc_dir)
print('installed %s sha16=%s' % (CAND, __import__('hashlib').sha256(open(dst, 'rb').read()).hexdigest()[:16]))

pyc = os.path.join(SP, REL.replace('\\', '/'))
out = os.path.join(ROOT, 'out', TAG, os.path.basename(REL).replace('.pyc', 'OK.py'))
os.makedirs(os.path.dirname(out), exist_ok=True)
if os.path.exists(out):
    os.remove(out)
r = subprocess.run([sys.executable, '-X', 'utf8', 'pycdc.py', '--region', '-o', out, pyc],
                   cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
if r.returncode != 0 or not os.path.exists(out):
    print('REGEN FAILED rc=%s\n%s\n%s' % (r.returncode, r.stdout[-3000:], r.stderr[-3000:]))
    sys.exit(1)
print('product=%s size=%d' % (out, os.path.getsize(out)))

unit = '<module>.RealtimeEventSource.clock_worker'
u = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(ROOT, 'work/unit_diff.py'),
                    pyc, unit, '--prod', out, '--all'], cwd=ROOT, capture_output=True,
                   text=True, encoding='utf-8')
print('---- unit_diff --all (summary) ----')
for ln in (u.stdout or '').splitlines():
    if ln.startswith('len ') or ln.startswith('==') or ln.startswith('hunks='):
        print(ln)
m = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(ROOT, 'work/allwin.py'),
                    pyc, unit, out], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
print('---- allwin (unfiltered) ----')
print((m.stdout or m.stderr[-3000:]).strip())
j = subprocess.run([sys.executable, '-X', 'utf8', 'scripts/pyc_verify.py', 'single', pyc,
                    '--source', out], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
print('---- judge ----')
for ln in (j.stdout or '').splitlines():
    if ln.startswith('[single] status=') or ': Failure' in ln or ': Missing' in ln or ': Extra' in ln:
        print(ln.strip())
print(j.stderr[-800:] if j.returncode != 0 else '')
