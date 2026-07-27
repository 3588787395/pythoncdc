"""R23-N7: 调试 400 <= e2.code <= 499 链式比较检测"""
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

    print(f"=== block@694 ===")
    for i in b694.instructions:
        print(f"  {i.offset:>5} {i.opname:<30} {i.argval!r}")
    print(f"succs: {[s.start_offset for s in b694.successors]}")
    print(f"block_role: {analyzer.get_block_role(b694)}")

    # Check chained compare detection
    cc_info = analyzer._detect_chained_compare_pattern(b694)
    print(f"\n_detect_chained_compare_pattern: {cc_info}")

    # Find IfRegion with condition_block = b694
    for region in analyzer.regions:
        if isinstance(region, IfRegion):
            if region.condition_block == b694:
                print(f"\n=== IfRegion with condition_block=b694 ===")
                print(f"  condition_block: {region.condition_block.start_offset}")
                print(f"  then_blocks: {[b.start_offset for b in region.then_blocks]}")
                print(f"  else_blocks: {[b.start_offset for b in region.else_blocks]}")
                print(f"  chained_compare_ops: {getattr(region, 'chained_compare_ops', None)}")
                print(f"  chained_compare_blocks: {[b.start_offset for b in getattr(region, 'chained_compare_blocks', [])]}")
                print(f"  chained_left_instr: {getattr(region, 'chained_left_instr', None)}")
                print(f"  chained_comparator_instrs: {getattr(region, 'chained_comparator_instrs', None)}")

    # Also check the successor block@720
    b720 = None
    for b in cfg.blocks.values():
        if b.start_offset == 720:
            b720 = b
            break
    if b720:
        print(f"\n=== block@720 (fallthrough) ===")
        for i in b720.instructions:
            print(f"  {i.offset:>5} {i.opname:<30} {i.argval!r}")
        print(f"succs: {[s.start_offset for s in b720.successors]}")
        print(f"block_role: {analyzer.get_block_role(b720)}")


if __name__ == '__main__':
    main()
