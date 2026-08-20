"""Trace finalbody generation for Region 3 (outer try-except-finally)"""
import sys
sys.path.insert(0, '.')

from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
import marshal, types

f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
f.close()

for c in code.co_consts:
    if isinstance(c, types.CodeType):
        for cc in c.co_consts:
            if isinstance(cc, types.CodeType) and cc.co_name == 'exception_handling_complex':
                target_code = cc
                break

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(target_code)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find Region 3 (outer try-except-finally)
for i, r in enumerate(analyzer.regions):
    if type(r).__name__ == 'TryExceptRegion' and getattr(r, 'has_finally', False):
        print(f"Region {i}: {type(r).__name__}")
        print(f"  entry: {r.entry.start_offset}")
        print(f"  try_offset: {r.try_offset_start}-{r.try_offset_end}")
        print(f"  try_blocks: {[b.start_offset for b in r.try_blocks]}")
        print(f"  else_blocks: {[b.start_offset for b in (r.else_blocks or [])]}")
        print(f"  finally_blocks: {[b.start_offset for b in r.finally_blocks]}")
        print(f"  finally_copy_blocks: {r.finally_copy_blocks}")
        print(f"  handler_entries: {[b.start_offset for b in r.handler_entry_blocks]}")
        
        # Check what _generate_handler_body_statements returns for finally blocks
        gen = RegionASTGenerator(cfg, analyzer)
        
        for fb in r.finally_blocks:
            print(f"\n  --- Finally block {fb.start_offset} ---")
            print(f"  Instructions:")
            for inst in fb.instructions:
                print(f"    {inst.offset:4d} {inst.opname:30s}")
            
            # Check if block is already generated
            print(f"  In generated_blocks: {fb in gen.generated_blocks}")
            
            # Try to generate
            stmts = gen._generate_handler_body_statements(fb)
            print(f"  Generated stmts: {stmts}")
        
        # Also check finally_copy_blocks
        for fc_offset, fc_keep in r.finally_copy_blocks.items():
            fc_block = cfg.get_block_by_offset(fc_offset)
            print(f"\n  --- Finally copy block {fc_offset} (keep={fc_keep}) ---")
            print(f"  Instructions:")
            for inst in fc_block.instructions:
                print(f"    {inst.offset:4d} {inst.opname:30s}")
        break
