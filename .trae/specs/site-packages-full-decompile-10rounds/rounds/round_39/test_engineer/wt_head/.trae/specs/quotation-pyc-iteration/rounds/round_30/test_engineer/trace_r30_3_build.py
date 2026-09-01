"""R30-3 调试：详细跟踪 IfRegion@384 的构建过程"""
import sys
sys.path.insert(0, '/workspace')
sys.path.insert(0, '/workspace/core')
from cfg.cfg_builder import build_cfg
from cfg.region_analyzer import RegionAnalyzer
import marshal, struct

with open('/workspace/quotation.pyc', 'rb') as f:
    f.read(4); flags = struct.unpack('<I', f.read(4))[0]
    f.read(8); code = marshal.load(f)

def find_code(co, name):
    if co.co_name == name: return co
    for const in co.co_consts:
        if hasattr(const, 'co_name'):
            r = find_code(const, name)
            if r: return r
    return None

target = find_code(code, 'get_stock_exrights')
cfg = build_cfg(target)

# Monkey-patch
orig_ncpd = RegionAnalyzer._find_nearest_common_post_dominator
def traced_ncpd(self, a, b):
    result = orig_ncpd(self, a, b)
    if a.start_offset in (484, 516, 384) or b.start_offset in (484, 516, 384):
        print(f"  [NCPD] a={a.start_offset} b={b.start_offset} -> {result.start_offset if result else None}")
    return result
RegionAnalyzer._find_nearest_common_post_dominator = traced_ncpd

orig_cmfjt = RegionAnalyzer._compute_merge_from_jump_targets
def traced_cmfjt(self, header, then_succ, else_succ):
    result = orig_cmfjt(self, header, then_succ, else_succ)
    if header.start_offset in (384, 342) or then_succ.start_offset in (484, 384) or else_succ.start_offset in (516, 520):
        print(f"  [_compute_merge_from_jump_targets] header={header.start_offset} "
              f"then_succ={then_succ.start_offset} else_succ={else_succ.start_offset} "
              f"-> {result.start_offset if result else None}")
    return result
RegionAnalyzer._compute_merge_from_jump_targets = traced_cmfjt

orig_build_basic = RegionAnalyzer._build_basic_if_region
def traced_build_basic(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block=None, boolop_regions=None, ternary_regions=None):
    if block.start_offset == 384:
        print(f"\n=== _build_basic_if_region called for block@384 ===")
        print(f"  then_blocks={[b.start_offset for b in then_blocks]}")
        print(f"  else_blocks={[b.start_offset for b in else_blocks]}")
        print(f"  merge={merge.start_offset if merge else None}")
    result = orig_build_basic(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block, boolop_regions, ternary_regions)
    if block.start_offset == 384:
        if result:
            print(f"  -> result: then={[b.start_offset for b in result.then_blocks] if result.then_blocks else None}")
            print(f"             else={[b.start_offset for b in result.else_blocks] if result.else_blocks else None}")
            print(f"             merge={result.merge_block.start_offset if result.merge_block else None}")
            print(f"             blocks={[b.start_offset for b in result.blocks]}")
    return result
RegionAnalyzer._build_basic_if_region = traced_build_basic

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
