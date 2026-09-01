"""R23-N7: 调试 IfRegion 中链式比较属性是否正确设置"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion

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

    # Find block@694 (the 400 <= e2.code <= 499 condition)
    b694 = None
    for b in cfg.blocks.values():
        if b.start_offset == 694:
            b694 = b
            break

    if not b694:
        print("block@694 not found")
        return

    # Find IfRegion with condition_block = b694 OR containing b694
    print("=== All IfRegions containing block@694 ===")
    for region in analyzer.regions:
        if isinstance(region, IfRegion):
            contains_694 = (region.condition_block == b694
                            or b694 in region.then_blocks
                            or b694 in region.else_blocks
                            or b694 in region.blocks)
            if contains_694:
                print(f"\n--- IfRegion ---")
                print(f"  entry: {region.entry.start_offset}")
                print(f"  condition_block: {region.condition_block.start_offset if region.condition_block else None}")
                print(f"  blocks: {sorted(b.start_offset for b in region.blocks)}")
                print(f"  then_blocks: {[b.start_offset for b in region.then_blocks]}")
                print(f"  else_blocks: {[b.start_offset for b in region.else_blocks]}")
                print(f"  region_type: {region.region_type}")
                print(f"  chained_compare_ops: {getattr(region, 'chained_compare_ops', 'MISSING')}")
                print(f"  chained_compare_blocks: {[b.start_offset for b in getattr(region, 'chained_compare_blocks', [])]}")
                print(f"  chained_left_instr: {getattr(region, 'chained_left_instr', 'MISSING')}")
                print(f"  chained_comparator_instrs: {getattr(region, 'chained_comparator_instrs', 'MISSING')}")
                print(f"  elif_conditions: {[b.start_offset for b in getattr(region, 'elif_conditions', [])]}")


if __name__ == '__main__':
    main()
