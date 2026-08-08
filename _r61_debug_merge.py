#!/usr/bin/env python3
"""R61: Debug the BoolOpRegion merge block processing"""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')

import marshal
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion
from pathlib import Path

pyc_path = Path("site-packages/IQEngine/plugins/plugin_system_accounts/position_model/live_future_position.pyc")

# Load code object from .pyc
with open(pyc_path, 'rb') as f:
    magic = f.read(4)
    flags = int.from_bytes(f.read(4), 'little')
    f.read(8)
    code = marshal.load(f)

# Find load_from_kwargs
def find_code(code, name):
    if code.co_name == name:
        return code
    for const in code.co_consts:
        if hasattr(const, 'co_name'):
            result = find_code(const, name)
            if result:
                return result
    return None

target_code = find_code(code, 'load_from_kwargs')
print(f"Found: {target_code.co_name}")

# Build CFG
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(target_code)

# Analyze regions
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find BoolOpRegion
for region in analyzer.regions:
    if isinstance(region, BoolOpRegion):
        print(f"\n=== BoolOpRegion ===")
        print(f"  entry: {region.entry.start_offset if region.entry else None}")
        print(f"  merge_block: {region.merge_block.start_offset if region.merge_block else None}")
        print(f"  value_target: {region.value_target}")
        print(f"  blocks: {[b.start_offset for b in region.blocks]}")
        if region.merge_block:
            print(f"\n  Merge block instructions:")
            for i in region.merge_block.instructions:
                if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                    argval = getattr(i, 'argval', getattr(i, 'arg', None))
                    print(f"    {i.offset:4d} {i.opname:30s} {argval}")
        print(f"  op_chain: {[(b.start_offset, op) for b, op in region.op_chain]}")
        if hasattr(region, 'prefix_block') and region.prefix_block:
            print(f"  prefix_block: {region.prefix_block.start_offset}")
        
        # Check what block 284 looks like in the CFG
        print(f"\n  All CFG blocks:")
        for b in cfg.blocks:
            print(f"    Block {b.start_offset}: ", end="")
            instrs = [i for i in b.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            print(", ".join(f"{i.opname}({getattr(i, 'argval', getattr(i, 'arg', '?'))})" for i in instrs[:5]))
            if len(instrs) > 5:
                print(f"      ... +{len(instrs)-5} more")
