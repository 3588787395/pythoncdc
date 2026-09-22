# -*- coding: utf-8 -*-
"""Round 33 target pool, read from the index the round-32 G6 batch wrote back (i.e. the landed
bytes -- core sha fa43dbc9e878eeacbfe0, commit 910a8f74).

  python -X utf8 pool33.py            # writes D:/Temp/r33gate/pool33.txt
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
mf = sum(e['matched_functions'] for e in idx)
assert mf == 5645, mf
assert all(e['last_tested_round'] == 32 for e in idx), 'index not stamped by round 32 G6'
core = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO).decode().strip()
sha = subprocess.check_output(['git', 'hash-object', '--',
                               'core/cfg/comprehension_generator.py'], cwd=REPO).decode().strip()
wt = io.open(os.path.join(REPO, 'core', 'cfg', 'comprehension_generator.py'), 'rb').read()
import hashlib
assert hashlib.sha256(wt).hexdigest()[:20] == 'fa43dbc9e878eeacbfe0', 'landed core moved'
assert hashlib.sha256(subprocess.check_output(
    ['git', 'cat-file', 'blob', 'HEAD:core/cfg/comprehension_generator.py'], cwd=REPO)
).hexdigest()[:20] == hashlib.sha256(wt.replace(b'\r\n', b'\n')).hexdigest()[:20], \
    'HEAD blob != measured worktree bytes'

partial = [e for e in idx if e['matched_functions'] < e['function_count']]
deficit = sum(e['function_count'] - e['matched_functions'] for e in partial)
d1 = [e for e in partial if e['function_count'] - e['matched_functions'] == 1]
d2 = [e for e in partial if e['function_count'] - e['matched_functions'] == 2]

out = [u'baseline(landed round32 index, HEAD %s, core sha fa43dbc9e878eeacbfe0): '
       u'files %d partial %d sum_deficit %d deficit1 %d deficit2 %d'
       % (core[:8], len(idx), len(partial), deficit, len(d1), len(d2))]
for e in sorted(partial, key=lambda e: (e['function_count'] - e['matched_functions'], e['path'])):
    d = e['function_count'] - e['matched_functions']
    p = e['path'] if e['path'].startswith('F:') else os.path.join(OUT, e['path'])
    out.append(u'  %-100s %d/%d  deficit %d' % (p.replace('\\', '/'),
                                                e['matched_functions'], e['function_count'], d))
text = u'\r\n'.join(out) + u'\r\n'
io.open(r'D:/Temp/r33gate/pool33.txt', 'wb').write(text.encode('utf-8'))
sys.stdout.reconfigure(encoding='utf-8')
print(text.splitlines()[0])
print('wrote D:/Temp/r33gate/pool33.txt  (%d partial rows, %d deficit1, %d deficit2)'
      % (len(partial), len(d1), len(d2)))
print('HEAD %s  core blob sha %s' % (core, sha[:12]))
