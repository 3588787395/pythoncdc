"""Trace _generate_try_body for exception_handling_complex."""
import sys, marshal, dis
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, IfRegion, LoopRegion

# Patch _generate_try_body to add tracing
import core.cfg.region_ast_generator as rag
orig_gen_try_body = rag.RegionASTGenerator._generate_try_body

def traced_gen_try_body(self, region):
    if region.entry and region.entry.start_offset == 26:
        print(f"\n=== _generate_try_body(region entry={region.entry.start_offset}) ===")
        print(f"  try_blocks: {[b.start_offset for b in region.try_blocks]}")
        print(f"  try_offset_start={region.try_offset_start}, try_offset_end={region.try_offset_end}")
        print(f"  has_finally={region.has_finally}, finally_blocks={[b.start_offset for b in getattr(region, 'finally_blocks', [])]}")
        print(f"  has_else={region.has_else}, else_blocks={[b.start_offset for b in getattr(region, 'else_blocks', [])]}")
        print(f"  children: {[(type(c).__name__, c.entry.start_offset if c.entry else 'NA') for c in getattr(region, 'children', [])]}")
        
        # Check nested try regions detection
        nested_try_regions = []
        for r in self.region_analyzer.regions:
            if isinstance(r, TryExceptRegion) and r is not region:
                is_child = r.parent is region
                is_in_try_blocks = r.entry in set(region.try_blocks)
                is_entry_in_handler = False
                for _, _, hblocks in region.except_handlers:
                    if r.entry in hblocks:
                        is_entry_in_handler = True
                        break
                if not is_entry_in_handler and getattr(region, 'finally_blocks', None):
                    if r.entry in set(region.finally_blocks):
                        is_entry_in_handler = True
                is_entry_in_else = bool(getattr(region, 'else_blocks', None) and r.entry in set(region.else_blocks))
                is_child_in_try = is_child and not is_entry_in_handler and not is_entry_in_else
                handler_in_range = False
                for heb in r.handler_entry_blocks:
                    if region.try_offset_start <= heb.start_offset < region.try_offset_end:
                        handler_in_range = True
                        break
                for _, _, hblocks in r.except_handlers:
                    for hb in hblocks:
                        if region.try_offset_start <= hb.start_offset < region.try_offset_end:
                            handler_in_range = True
                            break
                    if handler_in_range:
                        break
                is_before_try_start = r.entry.start_offset < region.try_offset_start and r.try_offset_end > region.try_offset_start
                is_nested = is_child_in_try or is_in_try_blocks or is_before_try_start or handler_in_range
                if is_nested and (r.parent is None or r.parent is region):
                    nested_is_smaller = r.try_offset_end - r.try_offset_start < region.try_offset_end - region.try_offset_start
                    if nested_is_smaller or is_child_in_try:
                        nested_try_regions.append(r)
                        print(f"  NESTED TRY: entry={r.entry.start_offset}, try_blocks={[b.start_offset for b in r.try_blocks]}, parent_is_region={r.parent is region}, is_child={is_child}, is_in_try_blocks={is_in_try_blocks}, is_child_in_try={is_child_in_try}, is_before_try_start={is_before_try_start}, handler_in_range={handler_in_range}")
        
        print(f"  nested_try_regions: {[r.entry.start_offset for r in nested_try_regions]}")
        
        # Check what IfRegions have entry matching try_blocks
        for block in sorted(region.try_blocks, key=lambda b: b.start_offset):
            for nr in self.region_analyzer.regions:
                if nr is region or nr.entry != block:
                    continue
                if isinstance(nr, TryExceptRegion):
                    continue
                _nr_parent = getattr(nr, 'parent', None)
                print(f"  BLOCK@{block.start_offset}: matches {type(nr).__name__}@{nr.entry.start_offset}, parent={type(_nr_parent).__name__ if _nr_parent else 'None'} parent_is_region={_nr_parent is region} parent_entry={_nr_parent.entry.start_offset if _nr_parent and _nr_parent.entry else 'NA'}")
    
    result = orig_gen_try_body(self, region)
    
    if region.entry and region.entry.start_offset == 26:
        print(f"\n  RESULT: {len(result)} stmts")
        for i, s in enumerate(result):
            print(f"    [{i}] type={s.get('type','?')}")
    
    return result

rag.RegionASTGenerator._generate_try_body = traced_gen_try_body

# Load and decompile
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
