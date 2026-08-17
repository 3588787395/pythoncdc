#!/usr/bin/env python3
"""Round 07: Trace block@566 ownership in TryExceptRegion(entry=474)."""
import sys, os, dis, types, marshal, struct
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion

PYC_PATH = str(PROJECT_ROOT / 'python_syntax_comprehensive_test.pyc')

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    return code

def collect_all_code_objects(code, prefix=''):
    from collections import OrderedDict
    result = OrderedDict()
    name = prefix + code.co_name if prefix else code.co_name
    result[name] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            child_prefix = prefix + code.co_name + '.' if prefix else code.co_name + '.'
            result.update(collect_all_code_objects(const, child_prefix))
    return result

def main():
    orig_code = load_code_from_pyc(PYC_PATH)
    all_codes = collect_all_code_objects(orig_code)
    target_name = '<module>.exception_handling_examples'
    target_code = all_codes[target_name]
    
    cfg = build_cfg(target_code)
    ra = RegionAnalyzer(cfg, parent_code=target_code)
    
    # Manually run analyze to trace
    ra.regions = []
    ra.block_to_region = {}
    
    # Run try_except identification
    try_regions = ra._identify_try_except_regions()
    
    # Check which region owns block@566
    blk_566 = cfg.get_block_by_offset(566)
    blk_622 = cfg.get_block_by_offset(622)
    blk_624 = cfg.get_block_by_offset(624)
    
    print("=== After _identify_try_except_regions ===")
    for r in try_regions:
        if isinstance(r, TryExceptRegion):
            print(f"\n  TryExceptRegion entry={r.entry.start_offset}:")
            print(f"    try_blocks: {[b.start_offset for b in r.try_blocks]}")
            print(f"    handler_entry_blocks: {[b.start_offset for b in r.handler_entry_blocks]}")
            print(f"    except_handlers: {[(et, en, [b.start_offset for b in hbs]) for et, en, hbs in r.except_handlers]}")
            print(f"    else_blocks: {[b.start_offset for b in r.else_blocks]}")
            print(f"    finally_blocks: {[b.start_offset for b in r.finally_blocks]}")
            print(f"    has_else: {r.has_else}")
            print(f"    all blocks: {[b.start_offset for b in r.blocks]}")
            if blk_566 in r.blocks:
                print(f"    *** block@566 IS in this region ***")
            if blk_622 in r.blocks:
                print(f"    *** block@622 IS in this region ***")
            if blk_624 in r.blocks:
                print(f"    *** block@624 IS in this region ***")
    
    print(f"\n  block@566 owner: {ra.block_to_region.get(blk_566)}")
    if ra.block_to_region.get(blk_566):
        _o = ra.block_to_region[blk_566]
        print(f"    type: {type(_o).__name__}, entry: {_o.entry.start_offset if _o.entry else None}")

if __name__ == '__main__':
    main()
