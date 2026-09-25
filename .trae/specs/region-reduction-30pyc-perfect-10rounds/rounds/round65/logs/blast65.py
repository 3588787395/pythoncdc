# -*- coding: utf-8 -*-
"""Product-level blast radius between two harness arms (reads h62 dumps + build dirs).

  python -X utf8 blast65.py <arm_a> <arm_b> <dump_a.jsonl> <dump_b.jsonl>

Uses h62.py's own product-naming rule (strip REPO/site-packages/, '/'->'__', ':'->'_',
'.pyc'->'OK.py') so a 'changed' verdict means the generated *OK.py bytes really differ.
Also prints the official instruction-gap sum |orig-decomp| per side.
"""
import hashlib
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
ROOT = r'D:/Temp/opencode/r65gate'
arm_a, arm_b, da, db = sys.argv[1:5]


def dst(arm, p):
    rel = p.replace('\\', '/')
    r0 = REPO.replace('\\', '/') + '/site-packages/'
    if rel.startswith(r0):
        rel = rel[len(r0):]
    name = rel.replace('/', '__')[:-4].replace(':', '_') + 'OK.py'
    return os.path.join(ROOT + '/build_' + arm, name).replace('\\', '/')


def load(p):
    out = {}
    for l in io.open(p, encoding='utf-8'):
        r = json.loads(l)
        out[r['path']] = r
    return out


A, B = load(da), load(db)
same = 0
diff = []
unresolved = []
for p in sorted(A):
    pa, pb = dst(arm_a, p), dst(arm_b, p)
    if not (os.path.isfile(pa) and os.path.isfile(pb)):
        unresolved.append(p)
        continue
    if hashlib.sha256(io.open(pa, 'rb').read()).hexdigest() == \
       hashlib.sha256(io.open(pb, 'rb').read()).hexdigest():
        same += 1
    else:
        diff.append(p)


def gap(rr):
    return sum(abs(x[1] - x[2]) for x in rr['mism'])


print('products identical=%d changed=%d unresolved=%d' % (same, len(diff), len(unresolved)))
for d in diff:
    print('   CHANGED', d.split('site-packages/')[-1])
for u in unresolved[:5]:
    print('   UNRESOLVED', u)
print('official instruction-gap sum %s=%d  %s=%d' % (arm_a, sum(gap(v) for v in A.values()),
                                                     arm_b, sum(gap(v) for v in B.values())))
print('matched functions %s=%d  %s=%d' % (arm_a, sum(v['matched_functions'] for v in A.values()),
                                          arm_b, sum(v['matched_functions'] for v in B.values())))
print('fully matched files %s=%d  %s=%d' % (arm_a, sum(1 for v in A.values() if not v['mism']),
                                            arm_b, sum(1 for v in B.values() if not v['mism'])))
for p in diff:
    print('--- %s' % p.split('site-packages/')[-1])
    print('    %s: %s' % (arm_a, sorted(map(repr, A[p]['mism']))))
    print('    %s: %s' % (arm_b, sorted(map(repr, B[p]['mism']))))
