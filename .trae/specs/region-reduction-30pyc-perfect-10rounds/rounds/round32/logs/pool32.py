# -*- coding: utf-8 -*-
"""Round 32 target pool, measured from the index the round-31 G6 batch wrote back (i.e. the
landed bytes -- core sha a66248d3b9a3e0a1, commit dca5bbff).

  python -X utf8 pool32.py            # writes D:/Temp/r32gate/pool32.txt
"""
import io
import json
import os
import subprocess
import sys

REPO = r'F:\Downloads\pythoncdc-main'
OUT = os.path.join(REPO, r'site-packages')

idx = json.load(io.open(os.path.join(REPO, 'pyc_index.json'), encoding='utf-8'))
assert isinstance(idx, list) and len(idx) == 402, len(idx)
tf = sum(e['function_count'] for e in idx)
assert tf == 5746, tf
core = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO).decode().strip()

partial = [e for e in idx if e['matched_functions'] < e['function_count']]
deficit = sum(e['function_count'] - e['matched_functions'] for e in partial)
d1 = [e for e in partial if e['function_count'] - e['matched_functions'] == 1]

out = [u'baseline(landed round31 index, HEAD %s): files %d partial %d sum_deficit %d deficit1 %d'
       % (core[:8], len(idx), len(partial), deficit, len(d1))]
for e in sorted(partial, key=lambda e: (e['function_count'] - e['matched_functions'], e['path'])):
    d = e['function_count'] - e['matched_functions']
    p = os.path.join(OUT, e['path']).replace('\\', '/') if not e['path'].startswith('F:') else e['path']
    out.append(u'  %-100s %d/%d  deficit %d' % (p, e['matched_functions'], e['function_count'], d))
text = u'\r\n'.join(out) + u'\r\n'
io.open(r'D:/Temp/r32gate/pool32.txt', 'wb').write(text.encode('utf-8'))
sys.stdout.reconfigure(encoding='utf-8')
print(text)
print('wrote D:/Temp/r32gate/pool32.txt  (%d partial rows)' % len(partial))
