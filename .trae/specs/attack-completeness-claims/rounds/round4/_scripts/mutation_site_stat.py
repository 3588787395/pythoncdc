#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：按「变异 site 文本」统计漏检/捕获（区分「值相等」与「值不等」两种成因）。"""
from __future__ import annotations

import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND4 = os.path.abspath(os.path.join(HERE, '..'))
JSONL = os.path.join(ROUND4, '_out', 'mutation_results.jsonl')
fam = sys.argv[1] if len(sys.argv) > 1 else 'd_int_to_bool'

rows = []
seen = set()
for line in open(JSONL, encoding='utf-8'):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    k = (r['pyc'], r['family'])
    if k in seen:
        continue
    seen.add(k)
    rows.append(r)
base = {r['pyc']: r for r in rows if r['family'] == 'BASELINE'}
green = {p for p, r in base.items() if r['status'] == 'success'}

c = collections.Counter()
for r in rows:
    if r['family'] != fam or r['pyc'] not in green:
        continue
    site = (r.get('site') or '').strip()
    # 把具体数字归一化
    import re
    key = re.sub(r'\b\d+\b', 'N', site)
    c[(key, r['status'])] += 1
for (k, st), n in sorted(c.items(), key=lambda kv: -kv[1]):
    print('%-6s %4d  %s' % (st, n, k))
