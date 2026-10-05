#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 3 站桩预处理：从 r1_residual_replay.json 提取 72 文件索引（拆 A/B 两半），
供 r2_regen_verify.py 分批重放（≤300s 约束）。"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
R1 = os.path.abspath(os.path.join(HERE, '..', 'round1'))

rows = json.load(open(os.path.join(R1, 'r1_residual_replay.json'), encoding='utf-8'))['rows']
paths = [{'path': r['pyc']} for r in rows]
half = (len(paths) + 1) // 2
for name, part in (('v2r3_residual_index_a.json', paths[:half]),
                   ('v2r3_residual_index_b.json', paths[half:])):
    with open(os.path.join(HERE, name), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(part, f, ensure_ascii=False, indent=1)
    print(name, len(part))
