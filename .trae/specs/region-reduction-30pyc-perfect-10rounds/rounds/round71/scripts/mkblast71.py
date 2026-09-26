# -*- coding: utf-8 -*-
"""Build logs/blast71_expected.json: for every shipped *OK.py whose bytes changed
between HEAD(R70) and the worktree(R71), record the adjudication that backs
'no hidden regression' (official-ruler movement + mandated-ruler status movement)."""
import io
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:\Downloads\pythoncdc-main'
C = r'D:/Temp/opencode/r71gate/center'


def jload(p):
    return [json.loads(l) for l in io.open(p, encoding='utf-8') if l.strip()]


changed = subprocess.run(['git', '-C', REPO, 'status', '--porcelain', 'site-packages'],
                         capture_output=True, text=True).stdout.splitlines()
changed = [l[3:].strip().replace('\\', '/') for l in changed if l.endswith('OK.py')]

A = {r['path'].replace('\\', '/'): r for r in jload(os.path.join(C, 'dump', 'landed56_r71.jsonl'))}
B = {r['path'].replace('\\', '/'): r for r in jload(os.path.join(C, 'dump', 'm71_56.jsonl'))}
g70 = json.load(io.open(r'F:/Downloads/pythoncdc-main/.trae/specs/region-reduction-30pyc-perfect-10rounds/'
                        r'rounds/round70/logs/gate/G3v_pycverify_r70.json', encoding='utf-8'))
g71 = json.load(io.open(os.path.join(C, 'logs', 'G3v_pycverify_r71.json'), encoding='utf-8'))
P = {r['pyc'].replace('\\', '/'): r for r in g70['rows']}
Q = {r['pyc'].replace('\\', '/'): r for r in g71['rows']}

out = {}
for rel in sorted(changed):
    pyc = REPO.replace('\\', '/') + '/site-packages/' + rel.split('site-packages/')[-1].replace('OK.py', '.pyc')
    bits = []
    if pyc in A:
        a, b = A[pyc], B[pyc]
        bits.append('official %s/%s -> %s/%s mism %d->%d' % (
            a['matched_functions'], a['total_functions'], b['matched_functions'],
            b['total_functions'], len(a['mism']), len(b['mism'])))
    else:
        bits.append('official: not in 56-target list (unchanged reading)')
    if pyc in P:
        bits.append('mandated %s->%s units %s/%s -> %s/%s' % (
            P[pyc]['status'], Q[pyc]['status'], P[pyc]['units_success'], P[pyc]['units_total'],
            Q[pyc]['units_success'], Q[pyc]['units_total']))
        if P[pyc]['status'] != Q[pyc]['status'] or P[pyc]['units_success'] != Q[pyc]['units_success']:
            def _names(row):
                out = set()
                for f in (row.get('failures') or []):
                    out.add(f.get('name') if isinstance(f, dict) else str(f))
                return out
            fn = sorted(_names(Q[pyc]) ^ _names(P[pyc]))
            bits.append('units_changed %s' % fn)
    else:
        bits.append('mandated: not in 402?')
    out[rel] = ' | '.join(bits)

p = os.path.join(C, 'logs', 'blast71_expected.json')
io.open(p, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
print('WROTE', p, 'entries=%d' % len(out))
for k, v in out.items():
    print('  %-70s %s' % (k.split('site-packages/')[-1], v))
