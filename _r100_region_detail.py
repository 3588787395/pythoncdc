#!/usr/bin/env python3
"""R100: Check region analysis for the if not include area"""
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

# Find IfRegions around 1008-1200
print("IfRegions with entry near 1000-1200:")
for i, r in enumerate(regions):
    if isinstance(r, IfRegion) and r.entry:
        eo = r.entry.start_offset
        if 1000 <= eo <= 1200:
            mb = r.merge_block.start_offset if r.merge_block else None
            tb = [b.start_offset for b in r.then_blocks]
            eb = [b.start_offset for b in r.else_blocks] if r.else_blocks else []
            cond = r.condition_block
            co_off = cond.start_offset if cond else None
            last = cond.get_last_instruction() if cond else None
            last_op = last.opname if last else 'NONE'
            last_arg = last.argval if last else None
            print(f"  [{i}] IfRegion@{eo} cond@{co_off} last={last_op}({last_arg})")
            print(f"    then={tb[:8]} else={eb[:8]} merge={mb}")
            
            # Check condition block instructions
            if cond:
                print(f"    cond instrs:")
                for ins in cond.instructions[-3:]:
                    print(f"      {ins.opname}({repr(ins.argval)[:30]})")
            
            # Check successors
            if cond and cond.successors:
                succs = [s.start_offset for s in cond.successors]
                print(f"    cond successors: {succs}")
                # Which successor is the then (fall-through) and which is else (jump target)?
                if last and 'IF_FALSE' in last.opname:
                    ft = succs[0] if succs else None  # fall-through = True branch
                    jt = last.argval  # jump target = False branch
                    print(f"    fall-through (True): {ft}, jump_target (False): {jt}")
            print()
