#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2 gate: small34 (34-set) two-half batch + compare vs v2 baseline (read-only)."""
import json
import os
import subprocess
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
HERE = os.path.join(ROOT, '.trae', 'specs', 'attain-true-completeness', 'rounds', 'round3')
BL = os.path.join(ROOT, '.trae', 'specs', 'adversarial-complete-forms-v2-10rounds', 'baseline')


def sh(args, timeout, label):
    t0 = time.time() if False else None
    import time as _t
    t0 = _t.time()
    r = subprocess.run([str(a) for a in args], cwd=ROOT, capture_output=True,
                       text=True, encoding='utf-8', errors='replace', timeout=timeout)
    out = (r.stdout or '') + (('\n[stderr] ' + r.stderr) if r.stderr else '')
    print('=== %s rc=%s %.1fs' % (label, r.returncode, _t.time() - t0))
    print(out[-1200:])
    return r.returncode, out


with open(os.path.join(BL, 'failing_index.json'), encoding='utf-8-sig') as f:
    paths34 = [e['path'] for e in json.load(f)]
reps = []
for tag, half in zip(('a', 'b'), (paths34[:17], paths34[17:])):
    out = os.path.join(HERE, 'small34_report_%s.json' % tag)
    sh([sys.executable, 'scripts/pyc_verify.py', 'batch', '--json', out] + half,
       300, 'SMALL34-' + tag.upper())
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
with open(os.path.join(HERE, 'small34_report_new.json'), 'w', encoding='utf-8') as f:
    json.dump(m, f, ensure_ascii=False, indent=1)
sh([sys.executable, 'scripts/pyc_verify.py', 'compare', '--before',
     os.path.join(BL, 'small_test_report.json'), '--after',
     os.path.join(HERE, 'small34_report_new.json')], 130, 'SMALL34-CMP')
print('small34 merged: units=%s/%s files_by_status=%s' % (
    m['units_success'], m['units_total'], m['files_by_status']))
