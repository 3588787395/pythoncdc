import sys, types, dis
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion
from core.cfg.code_generator import CodeGenerator

source = "def f():\n    try:\n        x = 1\n    except ValueError:\n        return 'val'\n    finally:\n        cleanup()"
code = compile(source, '<test>', 'exec')
f_code = [c for c in code.co_consts if isinstance(c, types.CodeType)][0]
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(f_code)

gen = RegionASTGenerator(cfg, recursive=True, parent_code=f_code)
regions = gen.region_analyzer.analyze()

print("BLOCKS:")
for block in cfg.get_blocks_in_order():
    print(f"  Block @ {block.start_offset}: {[(i.opname, i.argval) for i in block.instructions]}")
    print(f"    succs: {[b.start_offset for b in block.successors]}")

print("\nREGIONS:")
for i, r in enumerate(regions):
    if isinstance(r, TryExceptRegion):
        print(f"  Region[{i}]: try_offset={r.try_offset_start}-{r.try_offset_end}")
        print(f"    try_blocks: {[b.start_offset for b in r.try_blocks]}")
        print(f"    handler_entry_blocks: {[b.start_offset for b in r.handler_entry_blocks]}")
        print(f"    except_handlers: {r.except_handlers}")
        print(f"    has_finally={r.has_finally}")
        print(f"    finally_blocks: {[b.start_offset for b in r.finally_blocks] if r.finally_blocks else []}")
        print(f"    finally_copy_blocks: {r.finally_copy_blocks}")
        for b in r.try_blocks:
            print(f"    try_block {b.start_offset}: {[(i.opname, i.argval) for i in b.instructions]}")
        for b in r.handler_entry_blocks:
            print(f"    handler_block {b.start_offset}: {[(i.opname, i.argval) for i in b.instructions]}")
        if r.finally_blocks:
            for b in r.finally_blocks:
                print(f"    finally_block {b.start_offset}: {[(i.opname, i.argval) for i in b.instructions]}")
