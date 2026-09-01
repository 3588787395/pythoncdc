#!/usr/bin/env python3
"""检查 block 304 的 role 和其他属性。"""
import sys, marshal, types
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole

ORIG_PYC = "/workspace/quotation.pyc"

with open(ORIG_PYC, "rb") as f:
    f.read(16)
    code = marshal.load(f)

def find_code(c, name):
    for const in c.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            r = find_code(const, name)
            if r: return r
    return None

target_code = find_code(code, "get_growth_ability")
cfg = CFGBuilder().build(target_code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# 找 block 304
target_block = None
for b in cfg.blocks.values():
    if b.start_offset == 304:
        target_block = b
        break

# Check block role
role = analyzer.get_block_role(target_block)
print(f"block 304 role: {role}")
print(f"block 304 predecessors: {[b.start_offset for b in target_block.predecessors]}")
print(f"block 304 successors: {[b.start_offset for b in target_block.successors]}")
print(f"block 304 instructions:")
for ins in target_block.instructions:
    _argrepr = getattr(ins, 'argrepr', getattr(ins, 'arg', ''))
    print(f"  {ins.offset:4} {ins.opname:30} {_argrepr}")
print()

# Check effective_instructions
effective = analyzer.effective_instructions.get(target_block.start_offset)
print(f"effective_instructions[304]: {effective}")
print()

# Check IfRegion at 142 children
for r in analyzer.regions:
    if type(r).__name__ == 'IfRegion' and r.entry and r.entry.start_offset == 142:
        print(f"IfRegion at 142 children:")
        for c in (r.children or []):
            print(f"  {type(c).__name__}: entry={c.entry.start_offset if c.entry else None}")
        print()
        # Check if block 304 is in any child's blocks
        for c in (r.children or []):
            if target_block in c.blocks:
                print(f"  block 304 is in child {type(c).__name__} (entry={c.entry.start_offset if c.entry else None})")
        break

# Also check the outer IfRegion at 0
for r in analyzer.regions:
    if type(r).__name__ == 'IfRegion' and r.entry and r.entry.start_offset == 0:
        print(f"\nIfRegion at 0 children:")
        for c in (r.children or []):
            print(f"  {type(c).__name__}: entry={c.entry.start_offset if c.entry else None}")
        break

# Check what regions have block 304 in their children's blocks
print("\n=== Checking child_region_blocks for IfRegion at 142 ===")
for r in analyzer.regions:
    if type(r).__name__ == 'IfRegion' and r.entry and r.entry.start_offset == 142:
        child_region_blocks = set()
        child_entries = set()
        for child in (r.children or []):
            if isinstance(child, (type(r) if hasattr(r, 'LoopRegion') else None,)):
                pass
        # Manually check
        from core.cfg.region_analyzer import LoopRegion, TryExceptRegion, WithRegion, MatchRegion, BoolOpRegion, TernaryRegion
        for child in (r.children or []):
            if isinstance(child, (LoopRegion, TryExceptRegion, WithRegion, MatchRegion)):
                child_region_blocks.update(child.blocks)
                if child.entry:
                    child_entries.add(child.entry)
            elif isinstance(child, (BoolOpRegion, TernaryRegion)):
                child_region_blocks.update(child.blocks)
                if child.entry:
                    child_entries.add(child.entry)
        print(f"  block 304 in child_region_blocks: {target_block in child_region_blocks}")
        print(f"  block 304 in child_entries: {target_block in child_entries}")
        if target_block in child_region_blocks:
            for child in (r.children or []):
                if target_block in child.blocks:
                    print(f"  -> found in child: {type(child).__name__} (entry={child.entry.start_offset if child.entry else None})")
        break
