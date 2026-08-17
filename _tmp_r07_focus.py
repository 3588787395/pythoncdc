#!/usr/bin/env python3
"""Round 07: Focus on the try-except-else-finally structure issue."""
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
    
    # Find the main try-except-finally region (entry=286)
    for r in gen.region_analyzer.regions:
        if isinstance(r, TryExceptRegion) and r.entry and r.entry.start_offset == 286:
            print(f"=== Main TryExceptRegion (entry=286) ===")
            print(f"  try_blocks: {[b.start_offset for b in r.try_blocks]}")
            print(f"  try_offset_start: {r.try_offset_start}")
            print(f"  try_offset_end: {r.try_offset_end}")
            print(f"  handler_entry_blocks: {[b.start_offset for b in r.handler_entry_blocks]}")
            print(f"  except_handlers: {r.except_handlers}")
            print(f"  else_blocks: {[b.start_offset for b in r.else_blocks]}")
            print(f"  finally_blocks: {[b.start_offset for b in r.finally_blocks]}")
            print(f"  has_else: {r.has_else}")
            print(f"  has_finally: {r.has_finally}")
            print(f"  all blocks: {[b.start_offset for b in r.blocks]}")
            
            # Check which blocks in else_blocks belong to nested try regions
            print(f"\n  === Else blocks analysis ===")
            for eb in r.else_blocks:
                eb_region = gen.region_analyzer.get_region_for_block(eb)
                eb_entry_region = gen.region_analyzer.get_entry_region_for_block(eb)
                print(f"    Block@{eb.start_offset}: owner={type(eb_region).__name__ if eb_region else 'None'}, "
                      f"entry_region={type(eb_entry_region).__name__ if eb_entry_region else 'None'}")
            
            # Check nested try regions
            print(f"\n  === Nested TryExceptRegions ===")
            for nr in gen.region_analyzer.regions:
                if isinstance(nr, TryExceptRegion) and nr is not r:
                    if nr.entry and nr.entry.start_offset >= 286:
                        print(f"    TryExceptRegion entry={nr.entry.start_offset}: "
                              f"try_blocks={[b.start_offset for b in nr.try_blocks]}, "
                              f"try_offset_start={nr.try_offset_start}, "
                              f"try_offset_end={nr.try_offset_end}, "
                              f"handler_entry={[b.start_offset for b in nr.handler_entry_blocks]}, "
                              f"else_blocks={[b.start_offset for b in nr.else_blocks]}, "
                              f"finally_blocks={[b.start_offset for b in nr.finally_blocks]}")
            break
    
    # Also check the try-except region for block@150 (open file)
    for r in gen.region_analyzer.regions:
        if isinstance(r, TryExceptRegion) and r.entry and r.entry.start_offset == 150:
            print(f"\n=== File open TryExceptRegion (entry=150) ===")
            print(f"  try_blocks: {[b.start_offset for b in r.try_blocks]}")
            print(f"  try_offset_start: {r.try_offset_start}")
            print(f"  try_offset_end: {r.try_offset_end}")
            print(f"  else_blocks: {[b.start_offset for b in r.else_blocks]}")
            print(f"  has_else: {r.has_else}")
            break

if __name__ == '__main__':
    main()
