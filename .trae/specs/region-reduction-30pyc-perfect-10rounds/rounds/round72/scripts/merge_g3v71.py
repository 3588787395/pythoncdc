# -*- coding: utf-8 -*-
"""Merge the 8 mandated-ruler shard reports into logs/G3v_pycverify_r72.json
(shape identical to round70's G3v file) and print the round-over-round delta."""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
C = r'D:/Temp/opencode/r72gate/center'
rows = []
units_t = units_s = 0
fbs = {'success': 0, 'failure': 0, 'compile_error': 0, 'error': 0}
elapsed = 0.0
for i in range(8):
    r = json.load(io.open(os.path.join(C, 'chunks', 'rep%d.json' % i), encoding='utf-8'))
    rows.extend(r['rows'])
    units_t += r['units_total']
    units_s += r['units_success']
    elapsed += r.get('elapsed_sec', 0)
    for k in fbs:
        fbs[k] += r['files_by_status'].get(k, 0)
assert len(rows) == 402, len(rows)
rep = {
    'round': 72,
    'ruler': 'pylingual compare_pyc via scripts/pyc_verify.py',
    'units_total': units_t,
    'units_success': units_s,
    'success_rate': units_s / units_t,
    'files_by_status': fbs,
    'files': len(rows),
    'rows': rows,
    'shards': 8,
    'elapsed_sec': round(elapsed, 1),
}
out = os.path.join(C, 'logs', 'G3v_pycverify_r72.json')
io.open(out, 'w', encoding='utf-8').write(json.dumps(rep, ensure_ascii=False, indent=1))
print('WROTE', out)
print('files  success=%d failure=%d compile_error=%d error=%d / %d'
      % (fbs['success'], fbs['failure'], fbs['compile_error'], fbs['error'], len(rows)))
print('units  %d/%d = %.2f%%' % (units_s, units_t, 100.0 * units_s / units_t))

prev_p = r'F:/Downloads/pythoncdc-main/.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round71/logs/gate/G3v_pycverify_r71.json'
prev = json.load(io.open(prev_p, encoding='utf-8'))
po = {r['pyc']: r for r in prev['rows']}
no = {r['pyc']: r for r in rows}
green, red = [], []
for k in sorted(set(po) & set(no)):
    a, b = po[k], no[k]
    if a['status'] != b['status']:
        (green if b['status'] == 'success' else red).append((k, a['status'], b['status']))
print('status flips to success: %d' % len(green))
for k, a, b in green:
    print('  GREEN  %s  %s -> %s' % (k.split('site-packages/')[-1], a, b))
print('status flips to failure: %d' % len(red))
for k, a, b in red:
    print('  RED    %s  %s -> %s' % (k.split('site-packages/')[-1], a, b))
print('units r70 %d/%d -> r71 %d/%d (%+d)' % (
    prev['units_success'], prev['units_total'], units_s, units_t,
    units_s - prev['units_success'] * units_t // prev['units_total']))
io.open(os.path.join(C, 'logs', 'G3v_delta_r72.txt'), 'w', encoding='utf-8').write(
    'green=%d red=%d\n' % (len(green), len(red)) +
    ''.join('GREEN %s %s->%s\n' % (k, a, b) for k, a, b in green) +
    ''.join('RED %s %s->%s\n' % (k, a, b) for k, a, b in red))
