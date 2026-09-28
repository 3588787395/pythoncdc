# -*- coding: utf-8 -*-
"""Merge the 8 mandated-ruler shard reports into logs/G3v_pycverify_r74.json
and print the round-over-round delta against round73."""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
C = r'D:/Temp/opencode/r74gate/center'
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
    'round': 74,
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
out = os.path.join(C, 'logs', 'G3v_pycverify_r74.json')
os.makedirs(os.path.dirname(out), exist_ok=True)
io.open(out, 'w', encoding='utf-8', newline='\n').write(json.dumps(rep, ensure_ascii=False, indent=1))
print('WROTE', out)
print('files  success=%d failure=%d compile_error=%d error=%d / %d'
      % (fbs['success'], fbs['failure'], fbs['compile_error'], fbs['error'], len(rows)))
print('units  %d/%d = %.2f%%' % (units_s, units_t, 100.0 * units_s / units_t))

prev_p = (r'F:/Downloads/pythoncdc-main/.trae/specs/region-reduction-30pyc-perfect-10rounds'
          r'/rounds/round73/logs/gate/G3v_pycverify_r73.json')
prev = json.load(io.open(prev_p, encoding='utf-8'))
po = {r['pyc']: r for r in prev['rows']}
no = {r['pyc']: r for r in rows}
green, red = [], []
for k in sorted(set(po) & set(no)):
    a, b = po[k], no[k]
    if a['status'] != 'success' and b['status'] == 'success':
        green.append((k, a, b))
    elif a['status'] == 'success' and b['status'] != 'success':
        red.append((k, a, b))
moved = []
for k in sorted(set(po) & set(no)):
    a, b = po[k], no[k]
    if a['status'] == b['status'] and a['units_success'] != b['units_success']:
        moved.append((k, a, b))
L = ['G3v mandated delta round73 -> round74', '=' * 70,
     'prev  %d/%d = %.2f%%  success=%d failure=%d' % (
         prev['units_success'], prev['units_total'], 100.0 * prev['success_rate'],
         prev['files_by_status']['success'], prev['files_by_status']['failure']),
     'now   %d/%d = %.2f%%  success=%d failure=%d' % (
         units_s, units_t, 100.0 * units_s / units_t, fbs['success'], fbs['failure']),
     'net units %+d ; files success %+d' % (units_s - prev['units_success'],
                                            fbs['success'] - prev['files_by_status']['success']),
     '', 'turn green (%d):' % len(green)]
for k, a, b in green:
    L.append('  GREEN %-58s %s %d/%d -> %s %d/%d' % (
        k.split('site-packages/')[-1], a['status'], a['units_success'], a['units_total'],
        b['status'], b['units_success'], b['units_total']))
L.append('')
L.append('turn red (%d):' % len(red))
for k, a, b in red:
    L.append('  RED   %-58s %s %d/%d -> %s %d/%d' % (
        k.split('site-packages/')[-1], a['status'], a['units_success'], a['units_total'],
        b['status'], b['units_success'], b['units_total']))
L.append('')
L.append('same-status unit movement (%d):' % len(moved))
for k, a, b in moved:
    L.append('  MOVE  %-58s %s %d/%d -> %d/%d (%+d)' % (
        k.split('site-packages/')[-1], a['status'], a['units_success'], a['units_total'],
        b['units_success'], b['units_total'], b['units_success'] - a['units_success']))
L += ['', 'G3v verdict: %s' % ('PASS' if not red else 'FAIL (turn-red=%d)' % len(red))]
delta = os.path.join(C, 'logs', 'G3v_delta_r74.txt')
io.open(delta, 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
print('\n'.join(L[4:]))
print('WROTE', delta)
