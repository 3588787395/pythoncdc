"""Trace when block 806 gets marked as generated"""
import sys
sys.path.insert(0, '.')

from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, LoopRegion, IfRegion
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
import marshal, types, traceback

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

# Find the outer try-except-finally region
outer_region = None
for r in analyzer.regions:
    if isinstance(r, TryExceptRegion) and getattr(r, 'has_finally', False):
        outer_region = r
        break

block_806 = cfg.get_block_by_offset(806)
block_766 = cfg.get_block_by_offset(766)

# Use a tracking set
class TrackingSet(set):
    def add(self, block):
        if block is block_806:
            print(f"\n*** Block 806 added to generated_blocks! ***")
            traceback.print_stack()
        if block is block_766:
            print(f"\n*** Block 766 added to generated_blocks! ***")
            traceback.print_stack()
        super().add(block)
    
    def discard(self, block):
        if block is block_806:
            print(f"\n*** Block 806 discarded from generated_blocks! ***")
            traceback.print_stack()
        if block is block_766:
            print(f"\n*** Block 766 discarded from generated_blocks! ***")
            traceback.print_stack()
        super().discard(block)

gen = RegionASTGenerator(cfg, analyzer)
gen.generated_blocks = TrackingSet(gen.generated_blocks)

# Run generation
ast_dict = gen.generate()
print("\n=== Generation complete ===")
print(f"Block 806 in generated_blocks: {block_806 in gen.generated_blocks}")
print(f"Block 766 in generated_blocks: {block_766 in gen.generated_blocks}")
