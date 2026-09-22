# -*- coding: utf-8 -*-
"""Round 38 G1 rosters: the deficit-1 and deficit-2 file pools, read from the landed index.

usage: python -X utf8 g1lists38.py
"""
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
M = r'D:/Temp/r38gate/r38m'
sys.stdout.reconfigure(encoding='utf-8')

idx = json.load(io.open(os.path.join(REPO, 'pyc_index.json'), encoding='utf-8'))
assert len(idx) == 402 and sum(e['function_count'] for e in idx) == 5746
part = [e for e in idx if e['matched_functions'] < e['function_count']]


def rows(d):
    return [os.path.join(REPO, 'site-packages',
                         e['path'].replace('/', os.sep)).replace('\\', '/').replace('/', os.sep)
            for e in part if e['function_count'] - e['matched_functions'] == d]


for d, nm in ((1, 'd1_5'), (2, 'd2_11'), (3, 'd3'), (4, 'd4plus')):
    lst = rows(d) if d < 4 else [p for k in (4, 5, 6, 7, 14, 15) for p in rows(k)]
    if d == 3:
        lst = rows(3)
    if not lst:
        continue
    io.open(M + '/g1_%s.txt' % nm, 'w', encoding='utf-8', newline='').write('\n'.join(lst) + '\n')
    print('g1_%s.txt = %d rows' % (nm, len(lst)))

# the 8 rows of the round-38 target cluster (the one-deleted-JUMP_BACKWARD family), for G1-TARGET
CLUSTER = [
    'IQCommon/util/common_func.pyc',
    'IQData/plugins/plugin_system_realquote/real_quote.pyc',
    'IQData/utils/common_func.pyc',
    'fly/data/quote.pyc',
    'IQCommon/strategy/wizard_quant_api.pyc',
    'IQCommon/api/klinedata.pyc',
]
lst = [os.path.join(REPO, 'site-packages', p.replace('/', os.sep)) for p in CLUSTER]
assert all(os.path.isfile(p) for p in lst)
io.open(M + '/g1_cluster.txt', 'w', encoding='utf-8', newline='').write(
    '\n'.join(p.replace('\\', '/').replace('/', os.sep) for p in lst) + '\n')
print('g1_cluster.txt = %d rows (files carrying the 8-function cluster)' % len(lst))
