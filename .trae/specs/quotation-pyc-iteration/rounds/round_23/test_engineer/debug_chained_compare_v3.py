"""R23-N7: 检查 block@694 是否被 try_region claimed 导致跳过链式比较识别"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, TryExceptRegion

PYC = '/workspace/quotation.pyc'


def find_code_obj(co, name):
    for const in co.co_consts:
        if isinstance(const, type(co)):
            if const.co_name == name:
                return const
            sub = find_code_obj(const, name)
            if sub:
                return sub
    return None


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = find_code_obj(code_obj, 'api_get_financial')

    cfg = build_cfg(target)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    # Find block@694
    b694 = None
    for b in cfg.blocks.values():
        if b.start_offset == 694:
            b694 = b
            break

    if not b694:
        print("block@694 not found")
        return

    # Check if b694 is in any TryExceptRegion
    print("=== Regions containing block@694 ===")
    for region in analyzer.regions:
        if b694 in region.blocks:
            print(f"  {type(region).__name__} (entry={region.entry.start_offset if region.entry else None}): "
                  f"region_type={getattr(region, 'region_type', None)}")
            if isinstance(region, TryExceptRegion):
                print(f"    try_blocks: {[b.start_offset for b in region.try_blocks]}")
                print(f"    handler_blocks: {[b.start_offset for b in getattr(region, 'handler_blocks', [])]}")
                # Print all attributes
                for attr in dir(region):
                    if attr.startswith('_'):
                        continue
                    val = getattr(region, attr, None)
                    if isinstance(val, list) and val and hasattr(val[0], 'start_offset'):
                        try:
                            offsets = [b.start_offset for b in val]
                            if 694 in offsets:
                                print(f"    {attr} CONTAINS 694: {offsets}")
                        except Exception:
                            pass

    # Manually check _is_chained_compare_header
    print(f"\n=== _is_chained_compare_header(b694) ===")
    print(f"  {analyzer._is_chained_compare_header(b694)}")

    # Manually check _detect_chained_compare_pattern
    print(f"\n=== _detect_chained_compare_pattern(b694) ===")
    info = analyzer._detect_chained_compare_pattern(b694)
    print(f"  {info}")

    # Check if b694 was claimed
    # Manually re-create the claimed set used in _identify_chained_compare_regions
    # We need to look at the loop_regions, try_regions, with_regions, match_regions, assert_regions
    print(f"\n=== Check if b694 in any region that would claim it ===")
    # Note: try_regions, loop_regions, etc. are intermediate lists in analyze().
    # But TryExceptRegion is in self.regions, so let's check.
    in_try = False
    in_loop = False
    in_with = False
    in_assert = False
    for region in analyzer.regions:
        if b694 in getattr(region, 'blocks', set()):
            rtype = type(region).__name__
            if rtype == 'TryExceptRegion':
                in_try = True
            elif rtype == 'LoopRegion':
                in_loop = True
            elif rtype == 'WithRegion':
                in_with = True
            elif rtype == 'AssertRegion':
                in_assert = True
    print(f"  in_try={in_try}, in_loop={in_loop}, in_with={in_with}, in_assert={in_assert}")


if __name__ == '__main__':
    main()
