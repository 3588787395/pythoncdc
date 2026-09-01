"""Dump IfRegion@602 structure for get_option_info."""
import sys, dis, types
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion
from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

def find(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find(c, name)
            if r:
                return r
    return None

fn = find(code_obj, 'get_option_info')

cfg = CFGBuilder().build(fn)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find IfRegion@602
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 602:
        print(f"IfRegion@602:")
        print(f"  entry: {r.entry.start_offset}")
        print(f"  blocks: {sorted(b.start_offset for b in r.blocks)}")
        print(f"  then_blocks: {sorted(b.start_offset for b in r.then_blocks) if hasattr(r, 'then_blocks') and r.then_blocks else None}")
        print(f"  else_blocks: {sorted(b.start_offset for b in r.else_blocks) if hasattr(r, 'else_blocks') and r.else_blocks else None}")
        print(f"  merge_block: {r.merge_block.start_offset if r.merge_block else None}")
        print(f"  is_then_true: {getattr(r, 'is_then_true', 'N/A')}")
        print(f"  condition_jump_op: {getattr(r, 'condition_jump_op', 'N/A')}")
        # Print all attributes
        for attr in dir(r):
            if not attr.startswith('_') and attr not in ('blocks', 'then_blocks', 'else_blocks', 'entry', 'merge_block', 'parent', 'children', 'metadata'):
                val = getattr(r, attr)
                if not callable(val):
                    print(f"  {attr}: {val}")
        break

# Also find the inner LoopRegion@600
for r in analyzer.regions:
    if isinstance(r, LoopRegion) and r.header_block and r.header_block.start_offset == 600:
        print(f"\nLoopRegion@600:")
        print(f"  back_edge_block: {r.back_edge_block.start_offset if r.back_edge_block else None}")
        print(f"  body_blocks: {sorted(b.start_offset for b in r.body_blocks) if r.body_blocks else None}")
        print(f"  blocks: {sorted(b.start_offset for b in r.blocks)}")
        break
