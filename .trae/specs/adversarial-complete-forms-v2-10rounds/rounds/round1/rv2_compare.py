#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rv2 重放对比：rv2_replay_r78/r910（regen 后读数）vs r1_residual_replay（Round 1.1 基线）。"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

def load(p):
    return json.load(open(os.path.join(HERE, p), encoding='utf-8'))

base = {}
for row in load('r1_residual_replay.json')['rows']:
    base[row['pyc'].replace('\\', '/')] = (row['units_success'], row['units_total'])

cur = {}
for f in ('rv2_replay_r78.json', 'rv2_replay_r910.json'):
    for row in load(f):
        m = re.search(r'units=(\d+)/(\d+)', ' '.join(row.get('tail', [])))
        if m:
            cur[row['pyc'].replace('\\', '/')] = (int(m.group(1)), int(m.group(2)))

regressed, improved, missing = [], [], []
for pyc, (bs, bt) in sorted(base.items()):
    if pyc not in cur:
        missing.append(pyc)
        continue
    cs, ct = cur[pyc]
    if cs < bs:
        regressed.append((pyc, '%d/%d -> %d/%d' % (bs, bt, cs, ct)))
    elif cs > bs:
        improved.append((pyc, '%d/%d -> %d/%d' % (bs, bt, cs, ct)))

print('compared files: %d (missing in rv2: %d)' % (len(cur), len(missing)))
for p in missing:
    print('  MISSING %s' % p)
print('REGRESSED: %d' % len(regressed))
for p, d in regressed:
    print('  REGRESSED %s: %s' % (p, d))
print('IMPROVED: %d' % len(improved))
for p, d in improved:
    print('  IMPROVED %s: %s' % (p, d))
