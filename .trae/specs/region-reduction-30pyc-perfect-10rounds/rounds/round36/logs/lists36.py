# -*- coding: utf-8 -*-
"""Round 36 lists: rebuild the target-pool file lists from the freshly measured index, and copy
pool36.txt into place (pool36.py still writes it under the old scratch name).

  python -X utf8 lists36.py            # writes d1list.txt / d2list.txt / all402.txt / anchors105.txt / reprobat44.txt
"""
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r36gate/r36'
BS = os.sep


def w(name, lines):
    p = os.path.join(ROOT, name)
    io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    print('%-18s %4d lines  %s' % (name, len(lines), p))
    return p


idx = json.load(io.open(os.path.join(REPO, 'pyc_index.json'), encoding='utf-8'))
SP = os.path.join(REPO, 'site-packages')


def abspath(e):
    p = e['path']
    return p if os.path.isabs(p) else os.path.join(SP, p.replace('/', BS))


partial = [e for e in idx if e['matched_functions'] < e['function_count']]
d1 = [e for e in partial if e['function_count'] - e['matched_functions'] == 1]
d2 = [e for e in partial if e['function_count'] - e['matched_functions'] == 2]

# the round-35 baseline file was written under pool35.py's leftover name
src = os.path.join(r'D:/Temp/r36gate', 'pool35.txt')
dst = os.path.join(ROOT, 'pool36.txt')
if os.path.isfile(src):
    io.open(dst, 'wb').write(io.open(src, 'rb').read())
    print('pool36.txt copied (%d bytes)' % os.path.getsize(dst))

w('d1list.txt', [abspath(e) for e in sorted(d1, key=lambda e: e['path'])])
w('d2list.txt', [abspath(e) for e in sorted(d2, key=lambda e: e['path'])])
w('all402.txt', [abspath(e) for e in sorted(idx, key=lambda e: e['path'])])

# G3 = the 104 load-bearing anchors of round 34/35 + this round's now-fully-matched target.
prev = io.open(os.path.join(REPO, r'.trae/specs/region-reduction-30pyc-perfect-10rounds'
                            u'/rounds/round35/logs/anchors104.txt'), encoding='utf-8').read()
anchors = [l.strip() for l in prev.replace('\r\n', '\n').split('\n') if l.strip()]
assert len(anchors) == 104, len(anchors)
tgt = abspath([e for e in idx
               if e['path'].replace('\\', '/').endswith(
                   'IQEngine/plugins/plugin_system_risk_calculation/function.pyc')][0])
assert [e for e in idx if abspath(e) == tgt][0]['matched_functions'] == \
    [e for e in idx if abspath(e) == tgt][0]['function_count'], 'target not fully matched'
w('anchors105.txt', anchors + [tgt])

# G2' = round 35's 38-piece synthetic battery + its 5 new epilogue shapes.
bat = io.open(os.path.join(REPO, r'.trae/specs/region-reduction-30pyc-perfect-10rounds'
                           u'/rounds/round35/logs/reprobat39.txt'), encoding='utf-8').read()
lines = [l.strip() for l in bat.replace('\r\n', '\n').split('\n') if l.strip()]
assert len(lines) == 39, len(lines)
d = os.path.join(REPO, 'test_repros', 'round35_epilogue_duplicate_return')
new = [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith('.pyc')]
assert len(new) == 5, new
w('reprobat44.txt', lines + new)
