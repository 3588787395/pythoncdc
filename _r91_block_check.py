#!/usr/bin/env python3
"""R91 check block structure around offset 278"""
import sys, marshal, types
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

def find_function(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            inner = find_function(const, name)
            if inner:
                return inner
    return None

func_code = find_function(orig_code, 'get_price_common')
builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

# Show blocks around offset 260-300
print("=== Blocks around offset 260-300 ===")
for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    if 250 <= block.start_offset <= 300:
        instrs = [i for i in block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        print(f"\n  Block @offset={block.start_offset} (end={block.end_offset}):")
        for instr in instrs:
            argval = getattr(instr, 'argval', getattr(instr, 'arg', ''))
            print(f"    {instr.offset:4d} {instr.opname:30s} {argval}")
        print(f"    successors: {[s.start_offset for s in block.successors]}")
        print(f"    predecessors: {[p.start_offset for p in block.predecessors]}")
        role = analyzer.get_block_role(block)
        print(f"    block_role: {role}")

# Check the outer IfRegion
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 108:
        print(f"\n=== Outer IfRegion (entry=108) ===")
        print(f"  condition_block: {r.condition_block.start_offset}")
        print(f"  then_blocks: {[b.start_offset for b in r.then_blocks]}")
        print(f"  else_blocks: {[b.start_offset for b in r.else_blocks]}")
        
        # Check if block 278 is in then_blocks or else_blocks
        in_then = any(b.start_offset == 278 for b in r.then_blocks)
        in_else = any(b.start_offset == 278 for b in r.else_blocks)
        print(f"  block 278 in then: {in_then}, in else: {in_else}")
        
        # Check what happens at the end of then branch
        then_block_offsets = [b.start_offset for b in r.then_blocks]
        print(f"  last then block: {then_block_offsets[-1] if then_block_offsets else '?'}")
        break
