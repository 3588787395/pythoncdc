"""Debug get_price full analyze with R23N21_DEBUG."""
import sys
import types
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import (
    RegionAnalyzer, IfRegion, BoolOpRegion,
)


def main():
    pyc_path = '/workspace/quotation.pyc'
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = None
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'get_price':
            target = const
            break
    if target is None:
        print("get_price not found")
        return

    builder = CFGBuilder()
    cfg = builder.build(target)

    print(f"=== Full analyze (with R23N21_DEBUG) ===")
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    b0 = cfg.get_block_by_offset(0)
    print(f"\n=== Regions containing block 0 ===")
    for r in analyzer.regions:
        if b0 in r.blocks or (hasattr(r, 'entry') and r.entry == b0):
            rtype = type(r).__name__
            entry = r.entry.start_offset if r.entry else None
            print(f"  {rtype} entry={entry}")
            if isinstance(r, BoolOpRegion):
                print(f"    op_chain: {[(b.start_offset, op) for b, op in r.op_chain]}")
                print(f"    merge_block: {r.merge_block.start_offset if r.merge_block else None}")
            elif isinstance(r, IfRegion):
                print(f"    then_blocks: {[b.start_offset for b in r.then_blocks] if r.then_blocks else []}")
                print(f"    elif_conditions: {len(r.elif_conditions) if r.elif_conditions else 0}")
                print(f"    merge: {r.merge_block.start_offset if r.merge_block else None}")


if __name__ == '__main__':
    main()
