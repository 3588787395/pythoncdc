#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打印 l0_partition.json 中的 tie-resolved（平局裁决）明细，供报告引用。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.abspath(os.path.join(HERE, '..', 'logs', 'l0_partition.json'))
data = json.load(open(P, encoding='utf-8'))
want = sys.argv[1:] or None
for row in data:
    if 'error' in row:
        continue
    for r in row['rows']:
        for t in r.get('tie_resolved_blocks', []):
            tag = row['pyc'].split('/')[-1] + '::' + r['code']
            if want and not any(w in tag for w in want):
                continue
            print('--- %s @off=%d' % (tag, t['block_offset']))
            print('    claimants      = %s' % t['claimants'])
            print('    canonical      = %s (first-claimant-wins=%s)' % (
                t['canonical'], t['canonical_is_first']))
            print('    dyn_applies    = %s  scores=%s equal=%s' % (
                t['dynamic_priority_applies'], t['dynamic_scores'], t['scores_equal']))
