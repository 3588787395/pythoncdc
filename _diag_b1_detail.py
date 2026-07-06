import sys, os, dis, types
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion
from core.cfg.code_generator import CodeGenerator

# B1: try-finally-return
source = 'def f():\n    try:\n        return 1\n    finally:\n        pass'
code = compile(source, '<test>', 'exec')
cfg_builder = CFGBuilder()

f_code = None
for const in code.co_consts:
    if isinstance(const, types.CodeType):
        f_code = const
        break

cfg = cfg_builder.build(f_code)

gen = RegionASTGenerator(cfg, recursive=True, parent_code=f_code)
regions = gen.region_analyzer.analyze()

print("BLOCKS IN CFG:")
for block in cfg.get_blocks_in_order():
    print(f"  Block(offset={block.start_offset}): {[f'{i.opname}({i.argval!r})' for i in block.instructions]}")
    print(f"    successors: {[b.start_offset for b in block.successors]}")

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
        print(f"    cleanup_blocks: {[b.start_offset for b in r.cleanup_blocks] if r.cleanup_blocks else []}")
        for b in r.try_blocks:
            print(f"    try_block {b.start_offset}: {[f'{i.opname}({i.argval!r})' for i in b.instructions]}")

result = gen.generate()
code_gen = CodeGenerator()
decompiled = code_gen.generate(result)
print(f"\nDECOMPILED:\n{decompiled}")
