"""Trace _collect_branch_blocks for IfRegion@26."""
import sys, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, IfRegion

# Patch _collect_branch_blocks
import core.cfg.region_analyzer as ra
orig = ra.RegionAnalyzer._collect_branch_blocks

def traced(self, entry, merge, stop_set=None):
    result = orig(self, entry, merge, stop_set)
    if entry and entry.start_offset in (68, 284, 70):
        print(f"_collect_branch_blocks(entry={entry.start_offset}, merge={merge.start_offset if merge else 'NA'}, stop={sorted(s.start_offset for s in (stop_set or []))})")
        print(f"  => result={[b.start_offset for b in result]}")
    return result

ra.RegionAnalyzer._collect_branch_blocks = traced

f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
dp = [c for c in code.co_consts if hasattr(c, 'co_name') and c.co_name == 'DataProcessor'][0]
ehc = [c for c in dp.co_consts if hasattr(c, 'co_name') and c.co_name == 'exception_handling_complex'][0]

builder = CFGBuilder()
cfg = builder.build(ehc)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Check IfRegion@26
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 26:
        print(f"\nIfRegion@26: then_blocks={[b.start_offset for b in r.then_blocks]}")
        print(f"           else_blocks={[b.start_offset for b in r.else_blocks]}")
