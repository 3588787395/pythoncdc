#!/usr/bin/env python3
"""Debug: trace _generate_region for each child in else branch."""

import sys, os, marshal, types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion
from core.cfg.region_ast_generator import RegionASTGenerator, SHORT_CIRCUIT_JUMP_OPS

PYC_PATH = os.path.join(HERE, 'site-packages', 'IQEngine', 'utils', 'trade_schedule.pyc')

with open(PYC_PATH, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            sub = find_code(const, name)
            if sub:
                return sub
    return None

stt = find_code(code, 'is_stock_trade_trigger')

builder = CFGBuilder()
cfg = builder.build(stt)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find IfRegion@102
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 102:
        ifr = r
        break

ast_gen = RegionASTGenerator(cfg, analyzer)

# Generate then branch first
then_stmts = ast_gen._if_generate_then_branch(ifr)

# Now trace else branch
print("=== Tracing else branch ===")

# Patch _generate_region to trace calls
original_generate_region = ast_gen._generate_region
def traced_generate_region(region):
    entry_off = region.entry.start_offset if region.entry else None
    rtype = type(region).__name__
    
    # Check the conditions that should skip this region
    skip_reason = None
    if isinstance(region, IfRegion):
        # Check 1: entry owned by BoolOpRegion
        if region.entry is not None:
            _entry_owner = analyzer.block_to_region.get(region.entry)
            if isinstance(_entry_owner, BoolOpRegion) and _entry_owner is not region:
                skip_reason = f"entry owned by BoolOpRegion@{_entry_owner.entry.start_offset}"
        
        # Check 2: chained compare as BoolOp operand
        if not skip_reason and getattr(region, 'chained_compare_ops', None) and len(region.chained_compare_ops) >= 2:
            _cond_block = region.condition_block
            if _cond_block is not None:
                _cb_last = _cond_block.get_last_instruction()
                if _cb_last and _cb_last.opname in SHORT_CIRCUIT_JUMP_OPS:
                    _merge = getattr(region, 'merge_block', None)
                    if _merge is not None:
                        _merge_last = _merge.get_last_instruction()
                        if _merge_last and _merge_last.opname in SHORT_CIRCUIT_JUMP_OPS and _merge_last.opname not in ('JUMP_FORWARD',):
                            skip_reason = f"chained compare BoolOp operand (merge@{_merge.start_offset} ends with {_merge_last.opname})"
    
    print(f"  _generate_region({rtype}@{entry_off}) - skip_reason={skip_reason}")
    if isinstance(region, IfRegion):
        print(f"    chained_compare_ops={getattr(region, 'chained_compare_ops', None)}")
        print(f"    chained_compare_blocks={[b.start_offset for b in getattr(region, 'chained_compare_blocks', [])]}")
        print(f"    condition_block={region.condition_block.start_offset if region.condition_block else None}")
        _cb_last = region.condition_block.get_last_instruction() if region.condition_block else None
        print(f"    cond_block_last={_cb_last.opname if _cb_last else None}")
        print(f"    merge_block={region.merge_block.start_offset if region.merge_block else None}")
        _mb_last = region.merge_block.get_last_instruction() if region.merge_block else None
        print(f"    merge_block_last={_mb_last.opname if _mb_last else None}")
    
    result = original_generate_region(region)
    print(f"    result={type(result).__name__} len={len(result) if isinstance(result, list) else 1}")
    if result:
        for i, s in enumerate(result if isinstance(result, list) else [result]):
            t = s.get('type', '?') if isinstance(s, dict) else '?'
            print(f"      [{i}] type={t}")
    return result
ast_gen._generate_region = traced_generate_region

else_stmts = ast_gen._if_generate_else_branch(ifr)
print(f"\n  else_stmts = {else_stmts}")
