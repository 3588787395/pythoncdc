import io
import json
import os
import subprocess
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = r'F:\Downloads\pythoncdc-main'
HERE = os.path.join(ROOT, '.trae', 'specs', 'attain-true-completeness', 'rounds', 'round4')
BL = os.path.join(ROOT, '.trae', 'specs', 'adversarial-complete-forms-v2-10rounds', 'baseline')

paths = json.load(open(os.path.join(HERE, '_r4_paths34.json'), encoding='utf-8'))
reps = []
for tag, half in zip(('a', 'b'), (paths[:17], paths[17:])):
    out = os.path.join(HERE, 'r4_small34_report_%s.json' % tag)
    t0 = time.time()
    r = subprocess.run([sys.executable, '-X', 'utf8', 'scripts/pyc_verify.py', 'batch', '--json', out] + half,
                       cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=290)
    print('HALF', tag, 'rc=', r.returncode, '%.1fs' % (time.time() - t0))
    reps.append(out)

a = json.load(open(reps[0], encoding='utf-8'))
b = json.load(open(reps[1], encoding='utf-8'))
m = dict(a)
m['rows'] = a.get('rows', []) + b.get('rows', [])
for k in ('files_total', 'units_total', 'units_success'):
    m[k] = a.get(k, 0) + b.get(k, 0)
m['success_rate'] = m['units_success'] / m['units_total'] if m['units_total'] else 0.0
fbs = {}
for d in (a, b):
    for k, v in d.get('files_by_status', {}).items():
        fbs[k] = fbs.get(k, 0) + v
m['files_by_status'] = fbs
pbs = {}
for d in (a, b):
    for k, v in d.get('paths_by_status', {}).items():
        pbs.setdefault(k, []).extend(v)
m['paths_by_status'] = pbs
new = os.path.join(HERE, 'r4_small34_report_new.json')
json.dump(m, open(new, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('MERGED units', m['units_success'], '/', m['units_total'], 'files_by_status', fbs)

r = subprocess.run([sys.executable, '-X', 'utf8', 'scripts/pyc_verify.py', 'compare',
                    '--before', os.path.join(BL, 'small_test_report.json'),
                    '--after', new],
                   cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=130)
print('COMPARE rc=', r.returncode)
print((r.stdout or '')[-3000:])
print((r.stderr or '')[-1000:])
