# -*- coding: utf-8 -*-
"""Compare two harness record files (jsonl from r29.py run) path-by-path.

usage: cmp29.py <a.jsonl> <b.jsonl> [list-of-interest.txt]
prints: path  a matched/total  b matched/total  verdict  mism-a  mism-b
"""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')


def load(p):
    d = {}
    for line in io.open(p, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        d[r['path']] = r
    return d


a, b = load(sys.argv[1]), load(sys.argv[2])
want = None
if len(sys.argv) > 3:
    want = [l.strip() for l in io.open(sys.argv[3], encoding='utf-8') if l.strip()]


def row(p):
    ra, rb = a.get(p), b.get(p)
    if ra is None or rb is None:
        return 'MISSING %s a=%s b=%s' % (p, ra is not None, rb is not None)
    if ra.get('error') or rb.get('error'):
        return 'ERROR   %s a=%s b=%s' % (p, ra.get('error'), rb.get('error'))
    ta, tb = ra['total_functions'], rb['total_functions']
    ma, mb = ra['matched_functions'], rb['matched_functions']
    assert ta == tb, 'function count moved %s: %s vs %s' % (p, ta, tb)
    if mb > ma:
        v = 'IMPROVED'
    elif mb < ma:
        v = 'REGRESSION'
    elif json.dumps(ra.get('mism')) != json.dumps(rb.get('mism')):
        v = 'MOVED'
    else:
        v = 'SAME'
    return '%-10s %-62s a=%3d/%3d b=%3d/%3d  a_mism=%s b_mism=%s' % (
        v, p.split('site-packages/')[-1], ma, ta, mb, tb, ra.get('mism'), rb.get('mism'))


paths = want if want else sorted(set(a) | set(b))
tot = {'SAME': 0, 'IMPROVED': 0, 'REGRESSION': 0, 'MOVED': 0, 'other': 0}
for p in paths:
    s = row(p)
    k = s.split()[0]
    tot[k if k in tot else 'other'] += 1
    if k != 'SAME':
        print(s)
print('--- tally ---', json.dumps(tot))
