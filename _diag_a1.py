import sys, os, dis, types
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion

# A1: nested try with IndexError/AttributeError
source = 'try:\n    try:\n        pass\n    except IndexError:\n        pass\nexcept AttributeError:\n    pass'
code = compile(source, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print("REGIONS:")
for r in regions:
    print(f"  Region: {type(r).__name__}")
    if isinstance(r, TryExceptRegion):
        print(f"    try_offset: {r.try_offset_start}-{r.try_offset_end}")
        print(f"    try_blocks: {[b.start_offset for b in r.try_blocks]}")
        print(f"    except_handlers: {r.except_handlers}")
        print(f"    handler_entry_blocks: {[b.start_offset for b in r.handler_entry_blocks]}")
        print(f"    has_else: {r.has_else}")
        print(f"    has_finally: {r.has_finally}")
        print(f"    finally_blocks: {[b.start_offset for b in r.finally_blocks] if r.finally_blocks else []}")
        print(f"    else_blocks: {[b.start_offset for b in r.else_blocks] if r.else_blocks else []}")
        print(f"    cleanup_blocks: {[b.start_offset for b in r.cleanup_blocks] if r.cleanup_blocks else []}")
        print(f"    all blocks: {[b.start_offset for b in r.blocks]}")
        print(f"    parent: {type(r.parent).__name__ if r.parent else None}")
        for i, heb in enumerate(r.handler_entry_blocks):
            print(f"    handler_entry_block[{i}] @ offset {heb.start_offset}:")
            for instr in heb.instructions:
                print(f"      {instr.opname} {instr.argval!r}")

print("\nEXCEPTION TABLE:")
for entry in cfg.exception_table:
    print(f"  {entry}")
