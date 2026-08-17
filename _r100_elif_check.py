#!/usr/bin/env python3
"""R100: Check if/elif structure around blocks 1024-1200"""
import sys, types, marshal, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion

import json
with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

for entry in pyc_index:
    if 'api_base' in entry['path'] and entry['path'].endswith('.pyc') and 'IQData' in entry['path']:
        pyc_path = entry['path']
        break

with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

def extract(co):
    r = {co.co_name: co}
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r.update(extract(c))
    return r

om = extract(orig_code)
co = om['get_history_df']

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(co)
region_analyzer = RegionAnalyzer(cfg)
regions = region_analyzer.analyze()

blocks = {b.start_offset: b for b in cfg.get_blocks_in_order()}

# Find if regions around 1024-1200
print("IfRegions with entry near 1024-1200:")
for i, r in enumerate(regions):
    if isinstance(r, IfRegion) and r.entry:
        eo = r.entry.start_offset
        if 1000 <= eo <= 1300:
            mb = r.merge_block.start_offset if r.merge_block else None
            tb = [b.start_offset for b in r.then_blocks]
            eb = [b.start_offset for b in r.else_blocks] if r.else_blocks else []
            elif_conds = [b.start_offset for b in (getattr(r, 'elif_conditions', None) or [])]
            elif_bodies = [[b.start_offset for b in body] for body in (getattr(r, 'elif_bodies', None) or [])]
            print(f"  [{i}] IfRegion@{eo} then={tb[:5]} else={eb[:5]} merge={mb}")
            if elif_conds:
                print(f"    elif_conds={elif_conds}")
                for j, body in enumerate(elif_bodies):
                    print(f"    elif_bodies[{j}]={body[:5]}")

# Also show blocks 1034-1040 and 1142-1200 content
print(f"\nBlock@1024 (condition):")
for ins in blocks[1024].instructions:
    print(f"  {ins.opname}({repr(ins.argval)[:30]})")

print(f"\nBlock@1040 (then body):")
for ins in blocks[1040].instructions[:5]:
    print(f"  {ins.opname}({repr(ins.argval)[:30]})")

print(f"\nBlock@1098 (elif condition):")
for ins in blocks[1098].instructions[:5]:
    print(f"  {ins.opname}({repr(ins.argval)[:30]})")

print(f"\nBlock@1142 (elif then?):")
for ins in blocks[1142].instructions[:5]:
    print(f"  {ins.opname}({repr(ins.argval)[:30]})")

print(f"\nBlock@1200 (else/elif body):")
for ins in blocks[1200].instructions[:5]:
    print(f"  {ins.opname}({repr(ins.argval)[:30]})")
