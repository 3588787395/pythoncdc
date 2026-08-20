"""Trace which code path generates Try@70."""
import sys, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, IfRegion
import core.cfg.region_ast_generator as rag

# Patch _generate_try to trace
orig_gt = rag.RegionASTGenerator._generate_try
def traced_gt(self, region):
    if region.entry and region.entry.start_offset in (70, 290, 26):
        print(f"  _generate_try(entry={region.entry.start_offset}) called")
    result = orig_gt(self, region)
    if region.entry and region.entry.start_offset in (70, 290, 26):
        print(f"  _generate_try(entry={region.entry.start_offset}) => {result.get('type','?') if result else 'None'}")
    return result
rag.RegionASTGenerator._generate_try = traced_gt

# Patch _generate_region to trace
orig_gr = rag.RegionASTGenerator._generate_region
def traced_gr(self, region):
    if region.entry and region.entry.start_offset in (70, 290, 26):
        print(f"  _generate_region(entry={region.entry.start_offset}, type={type(region).__name__}) called")
    result = orig_gr(self, region)
    if region.entry and region.entry.start_offset in (70, 290, 26):
        print(f"  _generate_region(entry={region.entry.start_offset}) => done")
    return result
rag.RegionASTGenerator._generate_region = traced_gr

f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
dp = [c for c in code.co_consts if hasattr(c, 'co_name') and c.co_name == 'DataProcessor'][0]
ehc = [c for c in dp.co_consts if hasattr(c, 'co_name') and c.co_name == 'exception_handling_complex'][0]

builder = CFGBuilder()
cfg = builder.build(ehc)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

gen = rag.RegionASTGenerator(cfg, analyzer)
result = gen.generate()
