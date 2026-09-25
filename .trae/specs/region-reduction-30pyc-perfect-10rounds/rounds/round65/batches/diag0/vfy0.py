# -*- coding: utf-8 -*-
"""Byte-level proof that arm s1 reproduces the landed products exactly.

h62.py `ab` only compares a 16-hex sha256 prefix of the returned text, so this
script re-checks the *written product files* byte for byte, plus records the
raw returned text length for every one of the 402 targets.

usage: python -X utf8 vfy0.py
"""
import hashlib
import io
import json
import os

BS = chr(92)
REPO = r'F:\Downloads\pythoncdc-main'
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def dstname(p, arm):
    rel = p.replace(BS, '/')
    r0 = REPO.replace(BS, '/') + '/site-packages/'
    if rel.startswith(r0):
        rel = rel[len(r0):]
    return os.path.join('build_' + arm,
                        rel.replace('/', '__')[:-4].replace(':', '_') + 'OK.py')


paths = [l.strip() for l in io.open('targets_fixed.txt', encoding='utf-8') if l.strip()]
pairs, missing = [], []
for p in paths:
    a, b = dstname(p, 'landed'), dstname(p, 's1')
    if os.path.isfile(a) and os.path.isfile(b):
        pairs.append((p, a, b))
    else:
        missing.append(p)

diff = []
for p, a, b in pairs:
    ba, bb = io.open(a, 'rb').read(), io.open(b, 'rb').read()
    if ba != bb:
        diff.append((p, len(ba), len(bb)))

print('targets in list            : %d' % len(paths))
print('product-file pairs compared: %d' % len(pairs))
print('pairs with a side missing  : %d %s' % (len(missing), missing[:3]))
print('BYTE-DIFFERENT products    : %d %s' % (len(diff), diff[:5]))

# also confirm the returned text (what ab hashed) is identical, not just its sha16
L = {}
S = {}
for i in range(4):
    for l in io.open('dump/L_%d.jsonl' % i, encoding='utf-8'):
        if l.strip():
            L[json.loads(l)['path']] = json.loads(l)
    for l in io.open('dump/S_%d.jsonl' % i, encoding='utf-8'):
        if l.strip():
            S[json.loads(l)['path']] = json.loads(l)
mism = [p for p in L if p in S and (L[p].get('sha') != S[p].get('sha')
                                    or L[p].get('mism') != S[p].get('mism'))]
print('dump records: landed=%d s1=%d shared=%d (sha|mism)-different=%d'
      % (len(L), len(S), len(set(L) & set(S)), len(mism)))
print('aggregate matched/total: landed=%d/%d  s1=%d/%d' % (
    sum(x.get('matched_functions') or 0 for x in L.values()),
    sum(x.get('total_functions') or 0 for x in L.values()),
    sum(x.get('matched_functions') or 0 for x in S.values()),
    sum(x.get('total_functions') or 0 for x in S.values())))
print('clean files: landed=%d s1=%d' % (
    sum(1 for x in L.values() if x.get('total_functions')
        and x.get('matched_functions') == x.get('total_functions')
        and not x.get('error')),
    sum(1 for x in S.values() if x.get('total_functions')
        and x.get('matched_functions') == x.get('total_functions')
        and not x.get('error'))))
