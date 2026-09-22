# -*- coding: utf-8 -*-
"""Round 36 target pool, read from the index the round-35 G6 batch wrote back (i.e. the landed
bytes -- commit 703be216, core sha 92c8c2aabdcd37b9f32b).

  python -X utf8 pool36.py            # writes D:/Temp/r36gate/pool35.txt
"""
import hashlib
import io
import json
import os
import subprocess
import sys

REPO = r'F:\Downloads\pythoncdc-main'
OUT = os.path.join(REPO, r'site-packages')
REL = 'core/cfg/region_ast_generator.py'
LANDED_SHA = '92c8c2aabdcd37b9f32b'

idx = json.load(io.open(os.path.join(REPO, 'pyc_index.json'), encoding='utf-8'))
assert isinstance(idx, list) and len(idx) == 402, len(idx)
assert sum(e['function_count'] for e in idx) == 5746
assert sum(e['matched_functions'] for e in idx) == 5647
assert all(e['last_tested_round'] == 35 for e in idx), 'index not stamped by round 35 G6'
core = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO).decode().strip()
wt = io.open(os.path.join(REPO, 'core', 'cfg', 'region_ast_generator.py'), 'rb').read()
assert hashlib.sha256(wt).hexdigest()[:20] == LANDED_SHA, 'landed core moved'
assert hashlib.sha256(subprocess.check_output(
    ['git', 'cat-file', 'blob', 'HEAD:' + REL], cwd=REPO)).hexdigest()[:20] \
    == hashlib.sha256(wt.replace(b'\r\n', b'\n')).hexdigest()[:20], 'HEAD blob != worktree bytes'
assert not subprocess.check_output(['git', 'status', '--porcelain', '--', 'core'],
                                   cwd=REPO).decode().strip(), 'core/ dirty'

partial = [e for e in idx if e['matched_functions'] < e['function_count']]
deficit = sum(e['function_count'] - e['matched_functions'] for e in partial)
d1 = [e for e in partial if e['function_count'] - e['matched_functions'] == 1]
d2 = [e for e in partial if e['function_count'] - e['matched_functions'] == 2]

out = [u'baseline(landed round35 index, HEAD %s, core sha %s): '
       u'files %d partial %d sum_deficit %d deficit1 %d deficit2 %d'
       % (core[:8], LANDED_SHA, len(idx), len(partial), deficit, len(d1), len(d2))]
for e in sorted(partial, key=lambda e: (e['function_count'] - e['matched_functions'], e['path'])):
    d = e['function_count'] - e['matched_functions']
    p = e['path'] if e['path'].startswith('F:') else os.path.join(OUT, e['path'])
    out.append(u'  %-100s %d/%d  deficit %d' % (p.replace('\\', '/'),
                                                e['matched_functions'], e['function_count'], d))
text = u'\r\n'.join(out) + u'\r\n'
io.open(r'D:/Temp/r36gate/pool35.txt', 'wb').write(text.encode('utf-8'))
sys.stdout.reconfigure(encoding='utf-8')
print(text.splitlines()[0])
print('wrote D:/Temp/r36gate/pool35.txt  (%d partial rows, %d deficit1, %d deficit2)'
      % (len(partial), len(d1), len(d2)))
