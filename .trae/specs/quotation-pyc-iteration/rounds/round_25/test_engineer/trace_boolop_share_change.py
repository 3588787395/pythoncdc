"""R25: Trace BoolOp detection for share_change Block 114"""
import sys
import os
os.environ['R23N21_DEBUG'] = '1'

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

import types
target = None
for const in code_obj.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'share_change':
        target = const
        break

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(target)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Now check Block 114 specifically
blk114 = cfg.get_block_by_offset(114)
blk134 = cfg.get_block_by_offset(134)

print(f"\n=== Block 114 ===")
print(f"  last instr: {blk114.get_last_instruction().opname} -> {blk114.get_last_instruction().argval}")
print(f"  successors: {[s.start_offset for s in blk114.successors]}")
print(f"  conditional successors: {[s.start_offset for s in blk114.conditional_successors]}")
print(f"  in block_to_region: {blk114 in analyzer.block_to_region}")
r = analyzer.block_to_region.get(blk114)
print(f"  region: {type(r).__name__ if r else None}")

print(f"\n=== Block 134 ===")
print(f"  last instr: {blk134.get_last_instruction().opname} -> {blk134.get_last_instruction().argval}")
print(f"  successors: {[s.start_offset for s in blk134.successors]}")
print(f"  conditional successors: {[s.start_offset for s in blk134.conditional_successors]}")
print(f"  in block_to_region: {blk134 in analyzer.block_to_region}")
r = analyzer.block_to_region.get(blk134)
print(f"  region: {type(r).__name__ if r else None}")

# Try to detect boolop chain from Block 114 manually
print(f"\n=== Manual BoolOp detection from Block 114 ===")
claimed = set()
for region in analyzer.regions:
    for b in region.blocks:
        claimed.add(b)
print(f"  Block 114 in claimed: {blk114 in claimed}")

# Check what _detect_boolop_conditional_chain returns
chain = analyzer._detect_boolop_conditional_chain(blk114, claimed, skip_claimed_check=False)
print(f"  chain result: {[(b.start_offset, op) for b, op in chain] if chain else None}")

# Also try Block 134
print(f"\n=== Manual BoolOp detection from Block 134 ===")
chain134 = analyzer._detect_boolop_conditional_chain(blk134, claimed, skip_claimed_check=False)
print(f"  chain result: {[(b.start_offset, op) for b, op in chain134] if chain134 else None}")

# Check what _detect_boolop_chain_start returns
print(f"\n=== _detect_boolop_chain_start for Block 114 ===")
chain_start = analyzer._detect_boolop_chain_start(blk114, claimed)
print(f"  result: {[(b.start_offset, op) for b, op in chain_start] if chain_start else None}")

print(f"\n=== _detect_boolop_chain_start for Block 134 ===")
chain_start134 = analyzer._detect_boolop_chain_start(blk134, claimed)
print(f"  result: {[(b.start_offset, op) for b, op in chain_start134] if chain_start134 else None}")
