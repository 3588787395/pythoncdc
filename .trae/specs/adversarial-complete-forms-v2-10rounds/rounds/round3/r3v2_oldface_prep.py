#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建旧规范（harden-completed-forms-10rounds）round6-10 站桩面索引 + 基线读数。
输出：r3v2_oldface_index.json（唯一路径列表）、r3v2_oldface_baseline.json（path->units/status/failures）。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
R10 = os.path.join(ROOT, '.trae', 'specs', 'harden-completed-forms-10rounds', 'rounds', 'round10')

SRC = ['rv10_round6_full.json', 'rv10_round7_full.json', 'rv10_round8_full.json',
       'rv10_sentry.json', 'rv10_b72.json', 'rv10_b4846.json',
       'rv10_option.json', 'rv10_quotation.json']

seen = {}
order = []
for name in SRC:
    d = json.load(open(os.path.join(R10, name), encoding='utf-8'))
    for r in d.get('rows', []):
        p = r['pyc']
        if p not in seen:
            seen[p] = {'units_success': r.get('units_success'), 'units_total': r.get('units_total'),
                       'status': r.get('status'), 'failures': r.get('failures') or [], 'src': name}
            order.append(p)

index = [{'path': p} for p in order]
with open(os.path.join(HERE, 'r3v2_oldface_index.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(index, f, ensure_ascii=False, indent=1)
with open(os.path.join(HERE, 'r3v2_oldface_baseline.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(seen, f, ensure_ascii=False, indent=1)

half = (len(index) + 1) // 2
for nm, part in (('r3v2_oldface_index_a.json', index[:half]), ('r3v2_oldface_index_b.json', index[half:])):
    with open(os.path.join(HERE, nm), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(part, f, ensure_ascii=False, indent=1)
tot_u = sum(v['units_total'] or 0 for v in seen.values())
tot_s = sum(v['units_success'] or 0 for v in seen.values())
print('files=%d units=%d/%d  halves=%d/%d' % (len(index), tot_s, tot_u, len(index[:half]), len(index[half:])))