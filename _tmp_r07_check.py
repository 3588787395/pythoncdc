#!/usr/bin/env python3
"""Round 07: Check enclosing_try and block ownership."""
import sys, os, dis, types, marshal, struct
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import TryExceptRegion

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
    gen = RegionASTGenerator(cfg, recursive=False, parent_code=target_code)
    gen.region_analyzer.analyze()
    
    # Print all TryExceptRegions with details
    print("=== All TryExceptRegions ===")
    for r in gen.region_analyzer.regions:
        if not isinstance(r, TryExceptRegion):
            continue
        print(f"\n  TryExceptRegion entry={r.entry.start_offset if r.entry else None}:")
        print(f"    try_blocks: {[b.start_offset for b in r.try_blocks]}")
        print(f"    try_offset_start: {r.try_offset_start}")
        print(f"    try_offset_end: {r.try_offset_end}")
        print(f"    handler_entry_blocks: {[b.start_offset for b in r.handler_entry_blocks]}")
        print(f"    except_handlers: {[(et, en, [b.start_offset for b in hbs]) for et, en, hbs in r.except_handlers]}")
        print(f"    else_blocks: {[b.start_offset for b in r.else_blocks]}")
        print(f"    finally_blocks: {[b.start_offset for b in r.finally_blocks]}")
        print(f"    has_else: {r.has_else}")
        print(f"    has_finally: {r.has_finally}")
        print(f"    enclosing_try: {r.enclosing_try.entry.start_offset if r.enclosing_try and r.enclosing_try.entry else None}")
        print(f"    parent: {type(r.parent).__name__ if r.parent else None} (entry={r.parent.entry.start_offset if r.parent and hasattr(r.parent, 'entry') and r.parent.entry else None})")
        print(f"    all blocks: {[b.start_offset for b in r.blocks]}")
    
    # Check block_to_region for overlapping
    print("\n=== Block ownership map ===")
    for blk, reg in sorted(gen.region_analyzer.block_to_region.items(), key=lambda x: x[0].start_offset):
        if blk.start_offset >= 286:
            print(f"  Block@{blk.start_offset} -> {type(reg).__name__}(entry={reg.entry.start_offset if reg.entry else None})")

if __name__ == '__main__':
    main()
