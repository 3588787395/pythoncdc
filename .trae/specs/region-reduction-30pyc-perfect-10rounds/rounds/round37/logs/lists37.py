# -*- coding: utf-8 -*-
"""Round 37 lists: grow the two standing batteries by this round's handover item (R36 OUTCOME §六.6)
and re-cut the pool lists from the freshly measured index.

  G3: 105 load-bearing anchors + this round's now-fully-matched round-36 target  -> 106
  G2': round 36's 44-piece synthetic battery + its 7 new for-loop shapes         ->  51

  python -X utf8 lists37.py     # d1list / d2list / d17 / all402 / anchors106 / reprobat51
"""
import io
import json
import os

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r37gate/r37'
BS = os.sep
LOGS36 = os.path.join(REPO, r'.trae/specs/region-reduction-30pyc-perfect-10rounds'
                            u'/rounds/round36/logs')


def w(name, lines):
    p = os.path.join(ROOT, name)
    io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    print('%-18s %4d lines  %s' % (name, len(lines), p))
    return p


idx = json.load(io.open(os.path.join(REPO, 'pyc_index.json'), encoding='utf-8'))
assert isinstance(idx, list) and len(idx) == 402, len(idx)
assert all(e['last_tested_round'] == 36 for e in idx), 'index not stamped by round 36 G6'
SP = os.path.join(REPO, 'site-packages')


def abspath(e):
    p = e['path']
    return p if os.path.isabs(p) else os.path.join(SP, p.replace('/', BS))


partial = [e for e in idx if e['matched_functions'] < e['function_count']]
d1 = sorted([e for e in partial if e['function_count'] - e['matched_functions'] == 1],
            key=lambda e: e['path'])
d2 = sorted([e for e in partial if e['function_count'] - e['matched_functions'] == 2],
            key=lambda e: e['path'])
assert (len(partial), len(d1), len(d2)) == (28, 6, 11), (len(partial), len(d1), len(d2))

w('d1list.txt', [abspath(e) for e in d1])
w('d2list.txt', [abspath(e) for e in d2])
w('d17.txt', [abspath(e) for e in d1 + d2])
w('all402.txt', [abspath(e) for e in sorted(idx, key=lambda e: e['path'])])

# G3: round 36's 105 anchors + base.pyc, which round 36 flipped to fully matched
prev = io.open(os.path.join(LOGS36, 'anchors105.txt'), encoding='utf-8').read()
anchors = [l.strip() for l in prev.replace('\r\n', '\n').split('\n') if l.strip()]
assert len(anchors) == 105, len(anchors)
base = [e for e in idx if e['path'].replace('\\', '/').endswith(
    'IQEngine/plugins/plugin_fly_data/fly_api/base.pyc')]
assert len(base) == 1 and base[0]['matched_functions'] == base[0]['function_count'] == 41, base
tgt = abspath(base[0])
assert tgt not in anchors
w('anchors106.txt', anchors + [tgt])

# G2': round 36's 44-piece battery + the 7 for-loop-break-fold shapes it landed with
bat = io.open(os.path.join(LOGS36, 'reprobat44.txt'), encoding='utf-8').read()
lines = [l.strip() for l in bat.replace('\r\n', '\n').split('\n') if l.strip()]
assert len(lines) == 44, len(lines)
d = os.path.join(REPO, 'test_repros', 'round36_for_loop_dropped')
new = [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith('.pyc')]
assert len(new) == 7, new
w('reprobat51.txt', lines + new)
