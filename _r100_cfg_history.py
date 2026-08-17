#!/usr/bin/env python3
"""R100: Check CFG of get_history_df around block 1040"""
import sys, types, marshal, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

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
blocks = {b.start_offset: b for b in cfg.get_blocks_in_order()}

# Find blocks around offset 1040 and 1194
print(f"Total blocks: {len(blocks)}")
print(f"\nBlocks around offset 1040:")
for off in sorted(blocks.keys()):
    if 1020 <= off <= 1100:
        b = blocks[off]
        last = b.get_last_instruction()
        succs = [s.start_offset for s in b.successors]
        print(f"  Block@{off}: {len(b.instructions)} instrs, last={last.opname if last else 'NONE'}({repr(last.argval)[:20]}), succs={succs}")

print(f"\nBlocks around offset 1194:")
for off in sorted(blocks.keys()):
    if 1180 <= off <= 1240:
        b = blocks[off]
        last = b.get_last_instruction()
        succs = [s.start_offset for s in b.successors]
        print(f"  Block@{off}: {len(b.instructions)} instrs, last={last.opname if last else 'NONE'}({repr(last.argval)[:20]}), succs={succs}")

# Check what's at 1782 (the JUMP_FORWARD target in orig)
print(f"\nBlock at 1782:")
if 1782 in blocks:
    b = blocks[1782]
    print(f"  {len(b.instructions)} instrs, first 3:")
    for ins in b.instructions[:3]:
        print(f"    {ins.opname}({repr(ins.argval)[:30]})")
    last = b.get_last_instruction()
    print(f"  last: {last.opname}({repr(last.argval)[:20]})")
    print(f"  successors: {[s.start_offset for s in b.successors]}")
