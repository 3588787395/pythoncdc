# -*- coding: utf-8 -*-
"""RV2 driver (Task 5.3 复核整改): regen the 34-file failing_index, split in halves,
batch-verify, compare against baseline/small_test_report.json, print NEWFAIL and units delta.
Output: <specs round5>/r5v5fix2_batch34.json  (never touches r5v5fix_* / r5v5r_*).
"""
import json, os, subprocess, sys, tempfile

ROOT = r'f:\Downloads\pythoncdc-main'
SPEC = os.path.join(ROOT, '.trae', 'specs', 'adversarial-complete-forms-v2-10rounds')
IDX = os.path.join(SPEC, 'baseline', 'failing_index.json')
BASE = os.path.join(SPEC, 'baseline', 'small_test_report.json')
OUT = os.path.join(SPEC, 'rounds', 'round5', 'r5v5fix2_batch34.json')
CUT = 17


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def regen(pyc):
    ok = pyc[:-4] + 'OK.py'
    subprocess.run([sys.executable, os.path.join(ROOT, 'pycdc.py'), pyc, '-o', ok],
                   capture_output=True, text=True)


def run_half(paths, tag):
    out = os.path.join(tempfile.gettempdir(), 'r5fix2_half_%s.json' % tag)
    if os.path.exists(out):
        os.remove(out)
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                        'batch', '--json', out] + paths, cwd=ROOT, capture_output=True,
                       text=True, timeout=600, encoding='utf-8', errors='replace')
    print(r.stdout[-500:])
    if r.returncode != 0:
        print('[%s RC=%d] %s' % (tag, r.returncode, r.stderr[-500:]))
    return load(out)


def merge(a, b):
    m = dict(a)
    for k in ('rows',):
        m[k] = a[k] + b[k]
    for k in ('files_total', 'units_total', 'units_success'):
        m[k] = a[k] + b[k]
    m['success_rate'] = m['units_success'] / m['units_total'] if m['units_total'] else 0.0
    fbs = {}
    for d in (a, b):
        for k, v in d['files_by_status'].items():
            fbs[k] = fbs.get(k, 0) + v
    m['files_by_status'] = fbs
    pbs = {}
    for d in (a, b):
        for k, v in d.get('paths_by_status', {}).items():
            pbs.setdefault(k, []).extend(v)
    m['paths_by_status'] = pbs
    m['elapsed_sec'] = a.get('elapsed_sec', 0) + b.get('elapsed_sec', 0)
    return m


ents = load(IDX)
paths = [e['path'].replace('/', os.sep) for e in ents]
for p in paths:
    regen(p)
halves = [paths[:CUT], paths[CUT:]]
reps = [run_half(h, t) for h, t in zip(halves, ('a', 'b'))]
rep = merge(*reps)
with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(rep, f, ensure_ascii=False, indent=1)

base = load(BASE)
bmap = {r['pyc'].replace('\\', '/'): r for r in base['rows']}
nmap = {r['pyc'].replace('\\', '/'): r for r in rep['rows']}
newfail = []
for p, b in bmap.items():
    n = nmap.get(p)
    if n is None:
        newfail.append((p, 'MISSING', None, None))
        continue
    bu, nu = b.get('units_success', 0), n.get('units_success', 0)
    if nu < bu or (b.get('status') == 'success' and n.get('status') != 'success'):
        newfail.append((p, b.get('status'), bu, nu))
print('=== batch34 merged: %s units=%d/%d base_units=%d/%d ===' % (
    rep['files_by_status'], rep['units_success'], rep['units_total'],
    base['units_success'], base['units_total']))
print('NEWFAIL=%d' % len(newfail))
for p, st, bu, nu in newfail:
    print('  NEWFAIL', st, bu, '->', nu, p)
print('-> %s' % OUT)