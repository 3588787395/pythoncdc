"""R18: 检查 get_entry_region_for_block(164) 返回什么"""
import sys
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, BoolOpRegion, IfRegion
from core.cfg.cfg_builder import CFGBuilder


def main():
    module = load_pyc_file_v2('/workspace/quotation.pyc')
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = None
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'get_opt_objects':
            target = const
            break

    cfg = CFGBuilder().build(target)
    ra = RegionAnalyzer(cfg, parent_code=target)
    ra.analyze()

    blk_164 = cfg.get_block_by_offset(164)

    # Check all regions that match block 164 as entry
    print("=== Regions with is_block_entry(164) == True ===")
    for r in ra.regions:
        if r.is_block_entry(blk_164):
            print(f"  {type(r).__name__}: entry={r.entry.start_offset if r.entry else None}")

    # Check get_entry_region_for_block
    result = ra.get_entry_region_for_block(blk_164)
    print(f"\nget_entry_region_for_block(164) = {type(result).__name__} (entry={result.entry.start_offset if result and result.entry else None})")

    # Check get_region_for_block
    result2 = ra.get_region_for_block(blk_164)
    print(f"get_region_for_block(164) = {type(result2).__name__ if result2 else None} (entry={result2.entry.start_offset if result2 and result2.entry else None})")

    # Check the IfRegion at 0's children
    for r in ra.regions:
        if isinstance(r, IfRegion) and r.entry.start_offset == 0:
            print(f"\nIfRegion(0) children:")
            for c in (r.children or []):
                print(f"  {type(c).__name__}: entry={c.entry.start_offset if c.entry else None}")
            print(f"IfRegion(0) else_blocks: {[b.start_offset for b in r.else_blocks] if r.else_blocks else []}")


if __name__ == '__main__':
    main()
