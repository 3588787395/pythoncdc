"""Debug 3 failing ternary test cases."""
import sys
import os
import dis
import traceback
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, RegionType
from core.cfg.region_ast_generator import RegionASTGenerator

CASES = {
    "asyncio_gather": """import asyncio
async def main():
    return await asyncio.gather((f() if c else g()), h())
""",
    "contextlib_suppress": """from contextlib import suppress
with suppress((E1 if c else E2)):
    pass
""",
    "with_multiple_second_as": """with a as x, (b if c else d) as y:
    pass
""",
}

for name, source in CASES.items():
    print(f"\n{'='*60}")
    print(f"=== CASE: {name} ===")
    print(f"{'='*60}")
    code = compile(source, '<test>', 'exec')

    # Find nested code objects
    def find_codes(co, depth=0):
        print(f"{'  '*depth}code: {co.co_name}")
        for const in co.co_consts:
            if hasattr(const, 'co_code'):
                find_codes(const, depth+1)
    find_codes(code)

    # For asyncio_gather, the ternary is inside main()
    if name == "asyncio_gather":
        for const in code.co_consts:
            if hasattr(const, 'co_code') and const.co_name == 'main':
                code = const
                break

    print(f"\n=== Bytecode ({code.co_name}) ===")
    for instr in dis.get_instructions(code):
        print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argval}")

    # Build CFG and analyze regions
    builder = CFGBuilder()
    cfg = builder.build(code)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    print(f"\n=== Blocks ===")
    for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
        print(f"Block {block.start_offset} (end={block.end_offset}):")
        for instr in block.instructions:
            print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argval}")
        print()

    print(f"=== Regions ===")
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

    # Decompile
    print(f"\n=== Decompiling ===")
    try:
        gen = RegionASTGenerator(cfg, recursive=True, parent_code=code, top_level_code=code)
        ast_result = gen.generate()
        print(f"Result: {ast_result}")
    except Exception as e:
        print(f"EXCEPTION: {e}")
        traceback.print_exc()
