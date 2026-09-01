"""Trace block 584 processing in load_bars_from_hundsun."""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import (RegionAnalyzer, IfRegion, LoopRegion,
    BoolOpRegion, RegionType)
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = '/workspace/quotation.pyc'


def load_code(pyc_path):
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    for c in code_obj.co_consts:
        if isinstance(c, type(code_obj)) and c.co_name == 'load_bars_from_hundsun':
            return c
    return None


def main():
    co = load_code(PYC)
    cfg = build_cfg(co)
    ra = RegionAnalyzer(cfg)
    ra.analyze()

    # Find block 584
    block_584 = cfg.get_block_by_offset(584)
    print(f"=== Block 584 ===")
    print(f"  successors: {[s.start_offset for s in block_584.successors]}")
    print(f"  predecessors: {[p.start_offset for p in block_584.predecessors]}")

    # Find all regions that contain block 584
    print(f"\n=== Regions containing block 584 ===")
    for r in ra.regions:
        if block_584 in r.blocks:
            rtype = type(r).__name__
            entry = r.entry.start_offset if r.entry else None
            print(f"  {rtype} entry={entry} region_type={r.region_type}")
            if isinstance(r, BoolOpRegion):
                print(f"    BoolOp merge_block={r.merge_block.start_offset if r.merge_block else None}")
                print(f"    BoolOp blocks={sorted([b.start_offset for b in r.blocks])}")
            if isinstance(r, IfRegion):
                print(f"    IfRegion condition_block={r.condition_block.start_offset if r.condition_block else None}")
                print(f"    IfRegion then_blocks={[b.start_offset for b in r.then_blocks]}")
                print(f"    IfRegion elif_conditions={[b.start_offset for b in r.elif_conditions] if r.elif_conditions else None}")

    # Find regions with entry=584
    print(f"\n=== Regions with entry=584 ===")
    for r in ra.regions:
        if r.entry is block_584:
            rtype = type(r).__name__
            print(f"  {rtype} region_type={r.region_type}")

    # Find regions with merge_block=584
    print(f"\n=== Regions with merge_block=584 ===")
    for r in ra.regions:
        if hasattr(r, 'merge_block') and r.merge_block is block_584:
            rtype = type(r).__name__
            entry = r.entry.start_offset if r.entry else None
            print(f"  {rtype} entry={entry}")

    # Check parent IF_THEN at 214's children
    parent_region = None
    for r in ra.regions:
        if (isinstance(r, IfRegion)
                and r.entry is not None
                and r.entry.start_offset == 214):
            parent_region = r
            break

    if parent_region:
        print(f"\n=== Parent IF_THEN at 214 ===")
        print(f"  children: {[type(c).__name__ for c in (parent_region.children or [])]}")
        for c in (parent_region.children or []):
            entry = c.entry.start_offset if c.entry else None
            print(f"    {type(c).__name__} entry={entry}")
            if isinstance(c, BoolOpRegion):
                print(f"      merge_block={c.merge_block.start_offset if c.merge_block else None}")
                print(f"      blocks={sorted([b.start_offset for b in c.blocks])}")

    # Check get_entry_region_for_block(584)
    er = ra.get_entry_region_for_block(block_584)
    print(f"\n=== get_entry_region_for_block(584) ===")
    print(f"  {type(er).__name__ if er else None} entry={er.entry.start_offset if er and er.entry else None}")

    # Check get_region_for_block(584)
    br = ra.get_region_for_block(block_584)
    print(f"\n=== get_region_for_block(584) ===")
    print(f"  {type(br).__name__ if br else None} entry={br.entry.start_offset if br and br.entry else None}")


if __name__ == '__main__':
    main()
