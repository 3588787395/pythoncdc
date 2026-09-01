"""R30: Trace the exact code path for block 2660 IfRegion creation"""
import sys
sys.path.insert(0, '/workspace')

# Monkey-patch to trace
import core.cfg.region_analyzer as ra

original_build = ra.RegionAnalyzer._build_basic_if_region

def traced_build(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block=None, boundary_stop=None, ternary_regions=None, **kwargs):
    if hasattr(block, 'start_offset') and block.start_offset == 2660:
        print(f"\n=== TRACE _build_if_region_from_collected for block 2660 ===")
        print(f"  then_blocks={[b.start_offset for b in then_blocks]}")
        print(f"  else_blocks (before)={[b.start_offset for b in else_blocks]}")
        print(f"  merge={merge.start_offset if merge else None}")
        # Check what loop region contains this block
        for _r in self._filter_regions(list(self.block_to_region.values()), ra.LoopRegion):
            if block in _r.blocks:
                print(f"  In LoopRegion entry={_r.entry.start_offset if _r.entry else None}")
                print(f"    body_blocks={[b.start_offset for b in _r.body_blocks]}")
                print(f"    else_blocks={[b.start_offset for b in _r.else_blocks] if _r.else_blocks else []}")
                print(f"    block in body_blocks: {block in set(_r.body_blocks)}")
                print(f"    block == condition_block: {block == _r.condition_block}")
    result = original_build(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block=condition_block, boundary_stop=boundary_stop, ternary_regions=ternary_regions, **kwargs)
    if hasattr(block, 'start_offset') and block.start_offset == 2660:
        if hasattr(result, 'else_blocks'):
            print(f"  RESULT else_blocks={[b.start_offset for b in result.else_blocks]}")
            print(f"  RESULT type={result.region_type}")
    return result

ra.RegionAnalyzer._build_basic_if_region = traced_build

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

def find_code(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if hasattr(c, 'co_name'):
            r = find_code(c, name)
            if r:
                return r
    return None

module = load_pyc_file_v2('/workspace/quotation.pyc')
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()
co = find_code(code_obj, 'build_future_fill_time')
cfg = build_cfg(co)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()
