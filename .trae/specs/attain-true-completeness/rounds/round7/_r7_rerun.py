# -*- coding: utf-8 -*-
"""R6 helper: rebuild a probe batch command from an existing stamp JSON and run it.

Usage: python -X utf8 _r6_rerun.py <stamp_json> <new_stamp> [--stage <dir>] [--log <dir>]
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
os.chdir(ROOT)

src = sys.argv[1]
new_stamp = sys.argv[2]
stage = '.trae/specs/attain-true-completeness/test_repros/round6'
log = '.trae/specs/attain-true-completeness/rounds/round6'
if '--stage' in sys.argv:
    stage = sys.argv[sys.argv.index('--stage') + 1]
if '--log' in sys.argv:
    log = sys.argv[sys.argv.index('--log') + 1]

data = json.load(open(src, encoding='utf-8'))
args = []
for e in data:
    rel = e.get('pyc_src_rel') or ''
    if not rel:
        staged = e.get('staged_pyc') or ''
        rel = staged
    args.append('%s=%s' % (e['name'], rel))

cmd = [sys.executable, '-X', 'utf8',
       '.trae/specs/attain-true-completeness/rounds/round1/rec1_run.py',
       '--stage', stage, '--log', log, '--stamp', new_stamp] + args
print(' '.join(cmd[:8]), '... (%d probes)' % len(args))
p = subprocess.run(cmd, capture_output=True, cwd=ROOT, encoding='utf-8', errors='replace')
out = (p.stdout or '') + (p.stderr or '')
tail = [l for l in out.splitlines() if l.strip()][-40:]
print('\n'.join(tail))
