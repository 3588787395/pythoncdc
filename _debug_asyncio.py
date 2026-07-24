"""Trace ternary generation for asyncio_gather."""
import sys
import os
import dis
import traceback
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, RegionType, TernaryRegion
from core.cfg.region_ast_generator import RegionASTGenerator

SOURCE = """import asyncio
async def main():
    return await asyncio.gather((f() if c else g()), h())
"""

code = compile(SOURCE, '<test>', 'exec')
for const in code.co_consts:
    if hasattr(const, 'co_code') and const.co_name == 'main':
        code = const
        break

builder = CFGBuilder()
cfg = builder.build(code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("=== Regions ===")
for region in analyzer.regions:
    blocks_str = [b.start_offset for b in region.blocks] if hasattr(region, 'blocks') else 'N/A'
    print(f"  {region.region_type}: blocks={blocks_str}")
    if hasattr(region, 'condition_block') and region.condition_block:
        print(f"    cond_block: {region.condition_block.start_offset}")
    if hasattr(region, 'merge_block') and region.merge_block:
        print(f"    merge_block: {region.merge_block.start_offset}")
    if hasattr(region, 'merge_context'):
        print(f"    merge_context: {getattr(region, 'merge_context', None)}")
    if hasattr(region, 'value_target'):
        print(f"    value_target: {getattr(region, 'value_target', None)}")
    if hasattr(region, 'entry') and region.entry:
        print(f"    entry: {region.entry.start_offset}")
    if hasattr(region, 'merge_extra_blocks'):
        meb = getattr(region, 'merge_extra_blocks', None)
        if meb:
            print(f"    merge_extra_blocks: {[b.start_offset for b in meb]}")

# Find the ternary region
ternary_region = None
for r in analyzer.regions:
    if isinstance(r, TernaryRegion):
        ternary_region = r
        break

if ternary_region is None:
    print("NO TERNARY REGION FOUND")
else:
    print(f"\n=== Ternary Region ===")
    print(f"  entry: {ternary_region.entry.start_offset if ternary_region.entry else None}")
    print(f"  cond_block: {ternary_region.condition_block.start_offset if ternary_region.condition_block else None}")
    print(f"  merge_block: {ternary_region.merge_block.start_offset if ternary_region.merge_block else None}")
    print(f"  merge_context: {getattr(ternary_region, 'merge_context', None)}")
    print(f"  value_target: {getattr(ternary_region, 'value_target', None)}")

    print(f"\n=== Merge Block Instructions ===")
    if ternary_region.merge_block:
        for instr in ternary_region.merge_block.instructions:
            print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argval}")

    print(f"\n=== Merge Block Successors ===")
    if ternary_region.merge_block:
        for succ in ternary_region.merge_block.successors:
            print(f"  Successor block {succ.start_offset}:")
            for instr in succ.instructions:
                print(f"    {instr.offset:4d} {instr.opname:30s} {instr.argval}")

# Now try to generate AST with tracing
print(f"\n=== Generating AST ===")
gen = RegionASTGenerator(cfg, recursive=True, parent_code=code, top_level_code=code)

# Monkey-patch _generate_ternary to trace
orig_generate_ternary = gen._generate_ternary
def traced_generate_ternary(region, skip_store_targets=None):
    print(f"\n[TRACE] _generate_ternary called for region entry={region.entry.start_offset if region.entry else None}")
    print(f"[TRACE]   merge_block={region.merge_block.start_offset if region.merge_block else None}")
    print(f"[TRACE]   merge_context={getattr(region, 'merge_context', None)}")
    print(f"[TRACE]   value_target={getattr(region, 'value_target', None)}")
    # Trace ternary_expr construction
    try:
        # Build ternary_expr manually to see what it is
        _true_block = region.true_value_block if hasattr(region, 'true_value_block') else None
        _false_block = region.false_value_block if hasattr(region, 'false_value_block') else None
        print(f"[TRACE]   true_value_block={_true_block.start_offset if _true_block else None}")
        print(f"[TRACE]   false_value_block={_false_block.start_offset if _false_block else None}")
        if _true_block:
            print(f"[TRACE]   true_block instrs: {[(i.opname, i.argval) for i in _true_block.instructions if i.opname not in ('RESUME','NOP','CACHE','PUSH_NULL')]}")
        if _false_block:
            print(f"[TRACE]   false_block instrs: {[(i.opname, i.argval) for i in _false_block.instructions if i.opname not in ('RESUME','NOP','CACHE','PUSH_NULL')]}")
        # Trace cond_block
        _cond_block = region.condition_block
        if _cond_block:
            print(f"[TRACE]   cond_block instrs: {[(i.opname, i.argval) for i in _cond_block.instructions if i.opname not in ('RESUME','NOP','CACHE','PUSH_NULL')]}")
        # Trace func_call_info
        _fci = getattr(region, 'func_call_info', None)
        print(f"[TRACE]   func_call_info={_fci}")
        # Trace preload
        try:
            _preload = gen._compute_ternary_cond_preload_exprs(region)
            print(f"[TRACE]   preload_exprs={_preload}")
        except Exception as e:
            print(f"[TRACE]   preload error: {e}")
    except Exception as e:
        print(f"[TRACE] error inspecting: {e}")
    try:
        result = orig_generate_ternary(region, skip_store_targets)
        print(f"[TRACE] _generate_ternary returned: {result}")
        return result
    except Exception as e:
        print(f"[TRACE] _generate_ternary EXCEPTION: {e}")
        traceback.print_exc()
        raise
gen._generate_ternary = traced_generate_ternary

orig_build_no_target = gen._build_ternary_no_target_consumer_stmt
def traced_build_no_target(region, ternary_expr):
    print(f"\n[TRACE] _build_ternary_no_target_consumer_stmt called")
    print(f"[TRACE]   ternary_expr={ternary_expr}")
    try:
        result = orig_build_no_target(region, ternary_expr)
        print(f"[TRACE] _build_ternary_no_target_consumer_stmt returned: {result}")
        return result
    except Exception as e:
        print(f"[TRACE] _build_ternary_no_target_consumer_stmt EXCEPTION: {e}")
        traceback.print_exc()
        raise
gen._build_ternary_no_target_consumer_stmt = traced_build_no_target

try:
    ast_result = gen.generate()
    print(f"\n=== Final Result ===")
    print(f"Result: {ast_result}")
except Exception as e:
    print(f"EXCEPTION: {e}")
    traceback.print_exc()
