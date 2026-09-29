# -*- coding: utf-8 -*-
"""fix2: per-arm a/b/c/d/e readings table (archival evidence).

a = 官方 41 靶 h62 ab(list41 landed vs arm)
b = mandated list41 (mand_ab json: tiu units + CLEARED/NEW, ptradeAccount)
c = 金丝雀 h62 ab
d = battery worse
e = strict defects NEW/CLEARED
"""
import io
import json
import os
import subprocess
import sys

G = r'D:/Temp/opencode/r75gate'
D = os.path.join(G, 'fix2', 'dump')
sys.stdout.reconfigure(encoding='utf-8')

ARMS = ['pad8_1f', 'grp_g', 'editc9', 'ec_afgd4e', 'ec_afgd5e', 'ec_afgd5b']
STEM = {'pad8_1f': ['pad8_1f'], 'grp_g': ['grp_g'], 'editc9': ['editc9'],
        'ec_afgd4e': ['ecafd4e', 'ec_afgd4e'], 'ec_afgd5e': ['ecafd5e', 'ec_afgd5e'],
        'ec_afgd5b': ['ecafd5b', 'ec_afgd5b']}


def names(arm):
    return STEM.get(arm, [arm])


def first(paths):
    for q in paths:
        if os.path.exists(q):
            return q
    return None


def ab(a, b):
    r = subprocess.run([sys.executable, '-W', 'ignore', '-X', 'utf8',
                        os.path.join(G, 'center', 'h62.py'), 'ab', '--a=%s' % a, '--b=%s' % b],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout or ''
    tal = [l for l in out.splitlines() if l.startswith('TALLY')]
    fm = [l for l in out.splitlines() if l.startswith('files fully matched')]
    return (tal[0] if tal else 'n/a'), (fm[0] if fm else '')


def mand(arm):
    p = first([os.path.join(D, 'mand41_ab_%s.json' % n) for n in names(arm)])
    if not p:
        return 'n/a'
    d = json.load(io.open(p, encoding='utf-8'))
    key = [k for k in d if 'trade_info_utils' in k]
    if not key:
        return 'n/a'
    e = d[key[0]]
    cand_name = [k for k in e if k != 'landed'][-1]
    cand = e[cand_name]
    L = set(f[0] for f in e['landed']['fails'])
    C = set(f[0] for f in cand['fails'])
    pc = 'n/a'
    pkey = [k for k in d if 'ptradeAccount' in k]
    if pkey:
        pe = d[pkey[0]]
        pc = '%s->%s' % ('/'.join(map(str, pe['landed']['units'])),
                         '/'.join(map(str, pe[cand_name]['units'])))
    return 'tiu %s->%s  cleared=%d  ptrade %s' % (
        '/'.join(map(str, e['landed']['units'])), '/'.join(map(str, cand['units'])),
        len(L - C), pc)


def strict(arm):
    p = first([os.path.join(D, 'strict41_%s.json' % n) for n in names(arm)])
    if not p:
        return 'n/a'
    def load(q):
        a = json.load(io.open(q, encoding='utf-8'))
        out = {}
        for r in a:
            k = r['pyc'].split('/site-packages/')[-1]
            out[k] = set(tuple(x) for x in (r.get('bad') or []))
        return out
    L = load(os.path.join(D, 'strict41_landed.json'))
    C = load(p)
    new = clr = 0
    for k in set(L) | set(C):
        new += len(C.get(k, set()) - L.get(k, set()))
        clr += len(L.get(k, set()) - C.get(k, set()))
    return 'defects %d -> %d  NEW=%d CLEARED=%d' % (
        sum(len(v) for v in L.values()), sum(len(v) for v in C.values()), new, clr)


def canary(arm):
    cands = [os.path.join(D, 'canary_%s%s.jsonl' % (n, s))
             for n in names(arm) for s in ('', '_v2')]
    cands = [c for c in cands if os.path.exists(c)]
    head = os.path.join(G, 'fix1', 'dump', 'canary_head.jsonl')
    if not cands or not os.path.exists(head):
        return 'n/a'
    t, _ = ab(head, cands[-1])
    return t.replace('TALLY ', '')


lines = ['arm | a 官方41 ab | b mandated list41 | c 金丝雀 | e strict']
lines.append('---|---|---|---|---')
for arm in ARMS:
    f = first([os.path.join(D, 'list41_%s.jsonl' % n) for n in names(arm)])
    a = ab(os.path.join(D, 'list41_landed.jsonl'), f)[0].replace('TALLY ', '') if f else 'n/a'
    lines.append('%s | %s | %s | %s | %s' % (arm, a, mand(arm), canary(arm), strict(arm)))

lines.append('')
lines.append('p402 (402 支官方全量) landed vs arm:')
for stem in ['editc9', 'ecafd5e', 'ecafd5b', 'ecafd5b_v2', 'ecafd5b_v3']:
    f = os.path.join(D, 'p402_%s.jsonl' % stem)
    if os.path.exists(f):
        t, fm = ab(os.path.join(D, 'p402_landed.jsonl'), f)
        lines.append('  %-14s %s  %s' % (stem, t.replace('TALLY ', ''), fm))

lines.append('')
lines.append('asset_storage 单支（edit-D2 归因隔离，list1_asset）:')
for arm in ['landed', 'c9', 'gg', 't_A', 't_D', 't_D2', 'd5', 'd5e', 'd4e', 'd5b']:
    f = os.path.join(D, 'p1_asset_%s.jsonl' % arm)
    if os.path.exists(f):
        for l in io.open(f, encoding='utf-8'):
            r = json.loads(l)
            lines.append('  %-8s matched %s/%s mism=%s' % (arm, r['matched_functions'],
                                                           r['total_functions'], r['mism']))

txt = '\n'.join(lines) + '\n'
io.open(os.path.join(D, 'perarm75_fix2.txt'), 'w', encoding='utf-8', newline='\n').write(txt)
print(txt)
