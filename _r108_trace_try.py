"""Trace _generate_try_body for exception_handling_complex."""
import sys, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, IfRegion
import core.cfg.region_ast_generator as rag

orig = rag.RegionASTGenerator._generate_try_body

def traced(self, region):
    if region.entry and region.entry.start_offset == 26:
        print(f"\n=== _generate_try_body(entry=26) ===")
        print(f"  try_blocks: {[b.start_offset for b in region.try_blocks]}")
        # Check IfRegion@26 children
        for r in self.region_analyzer.regions:
            if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 26:
                print(f"  IfRegion@26: then={[b.start_offset for b in r.then_blocks]}, else={[b.start_offset for b in r.else_blocks]}")
                print(f"  IfRegion@26 children: {[type(c).__name__+'@'+str(c.entry.start_offset if c.entry else 'NA') for c in getattr(r,'children',[])]}")
    result = orig(self, region)
    if region.entry and region.entry.start_offset == 26:
        print(f"  RESULT: {len(result)} stmts")
        for i, s in enumerate(result):
            print(f"    [{i}] type={s.get('type','?')}")
    return result

rag.RegionASTGenerator._generate_try_body = traced

f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
dp = [c for c in code.co_consts if hasattr(c, 'co_name') and c.co_name == 'DataProcessor'][0]
ehc = [c for c in dp.co_consts if hasattr(c, 'co_name') and c.co_name == 'exception_handling_complex'][0]

builder = CFGBuilder()
cfg = builder.build(ehc)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

from core.cfg.region_ast_generator import RegionASTGenerator
gen = RegionASTGenerator(cfg, analyzer)
result = gen.generate()
