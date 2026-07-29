"""R30: Trace IfRegion creation for block 2660 in build_future_fill_time"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import (RegionAnalyzer, LoopRegion, IfRegion,
    RegionType, FORWARD_CONDITIONAL_JUMP_OPS, BlockRole)

PYC = '/workspace/quotation.pyc'


def find_code(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if hasattr(c, 'co_name'):
            r = find_code(c, name)
            if r:
                return r
    return None


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    co = find_code(code_obj, 'build_future_fill_time')
    cfg = build_cfg(co)

    b2660 = cfg.get_block_by_offset(2660)
    b2664 = cfg.get_block_by_offset(2664)
    b2746 = cfg.get_block_by_offset(2746)
    b2786 = cfg.get_block_by_offset(2786)

    print("=== Block 2660 info ===")
    print(f"  successors: {[s.start_offset for s in b2660.successors]}")
    print(f"  predecessors: {[p.start_offset for p in b2660.predecessors]}")
    print(f"  conditional_successors: {[s.start_offset for s in b2660.conditional_successors]}")

    print("\n=== Block 2664 info ===")
    print(f"  successors: {[s.start_offset for s in b2664.successors]}")
    print(f"  immediate_post_dominator: {b2664.immediate_post_dominator.start_offset if b2664.immediate_post_dominator else None}")

    print("\n=== Block 2746 info ===")
    print(f"  successors: {[s.start_offset for s in b2746.successors]}")
    print(f"  immediate_post_dominator: {b2746.immediate_post_dominator.start_offset if b2746.immediate_post_dominator else None}")
    print(f"  predecessors: {[p.start_offset for p in b2746.predecessors]}")

    print("\n=== Block 2786 info ===")
    print(f"  successors: {[s.start_offset for s in b2786.successors]}")
    print(f"  immediate_post_dominator: {b2786.immediate_post_dominator.start_offset if b2786.immediate_post_dominator else None}")

    # Manually compute NCPD
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    # Check block_to_region for 2660 and 2746
    print("\n=== block_to_region ===")
    for b in [b2660, b2664, b2746, b2786]:
        r = analyzer.block_to_region.get(b)
        rtype = type(r).__name__ if r else 'None'
        entry = r.entry.start_offset if r and hasattr(r, 'entry') and r.entry else 'None'
        print(f"  block {b.start_offset}: region={rtype} entry={entry}")

    # Check what region claims block 2746
    print("\n=== Checking if block 2746 is claimed ===")
    for r in analyzer.regions:
        if b2746 in r.blocks:
            rtype = type(r).__name__
            entry = r.entry.start_offset if hasattr(r, 'entry') and r.entry else 'None'
            print(f"  block 2746 is in {rtype} entry={entry}")

    # Manually test NCPD
    ncpd = analyzer._find_nearest_common_post_dominator(b2664, b2746)
    print(f"\nNCPD(2664, 2746) = {ncpd.start_offset if ncpd else None}")

    # Test _collect_branch_blocks for else
    else_stop = {b2664}
    else_blocks = analyzer._collect_branch_blocks(b2746, b2786, else_stop)
    print(f"\n_collect_branch_blocks(2746, 2786, {{2664}}) = {[b.start_offset for b in else_blocks]}")

    # Check block roles
    print("\n=== Block roles ===")
    for off in [2660, 2664, 2746, 2786]:
        role = analyzer.block_roles.get(off)
        print(f"  block {off}: role={role}")


if __name__ == '__main__':
    main()
