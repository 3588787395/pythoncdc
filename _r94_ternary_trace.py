#!/usr/bin/env python3
"""R94: Trace the TERNARY region that covers Block@800 in get_kline_by_date_one"""
import sys, types, marshal
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TernaryRegion, TryExceptRegion

pyc_path = "F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc"

def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

orig_code = load_pyc(pyc_path)

def extract_code_objects(code):
    result = {code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const))
    return result

orig_map = extract_code_objects(orig_code)
co = orig_map['get_kline_by_date_one']

cfg = build_cfg(co)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find block at offset 800
block_800 = None
for b in cfg.blocks.values():
    if b.start_offset == 800:
        block_800 = b
        break

if block_800 is None:
    print("Block@800 not found! Available offsets:")
    for b in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
        print(f"  {b.start_offset}")
else:
    print(f"Block@800: {block_800}")
    print(f"Block@800 role: {analyzer.get_block_role(block_800)}")
    print(f"Block@800 successors: {[s.start_offset for s in block_800.successors]}")

# Find TERNARY regions
for region in analyzer.regions:
    if isinstance(region, TernaryRegion):
        block_offsets = [b.start_offset for b in region.blocks]
        if block_800 and block_800 in region.blocks:
            print(f"\n=== TERNARY region containing Block@800 ===")
            print(f"  entry: {region.entry}")
            print(f"  entry.start_offset: {region.entry.start_offset if region.entry else None}")
            print(f"  blocks: {block_offsets}")
            print(f"  merge_block: {region.merge_block}")
            if hasattr(region, 'true_value_blocks'):
                print(f"  true_value_blocks: {[b.start_offset for b in region.true_value_blocks]}")
            if hasattr(region, 'false_value_blocks'):
                print(f"  false_value_blocks: {[b.start_offset for b in region.false_value_blocks]}")
            if hasattr(region, 'cond_block'):
                print(f"  cond_block: {region.cond_block}")
            if hasattr(region, 'condition_blocks'):
                print(f"  condition_blocks: {[b.start_offset for b in region.condition_blocks]}")
            
            # Print all attributes
            print(f"\n  All attributes:")
            for attr in sorted(dir(region)):
                if not attr.startswith('_') and attr not in ('blocks', 'entry'):
                    try:
                        val = getattr(region, attr)
                        if not callable(val):
                            if hasattr(val, 'start_offset'):
                                print(f"    {attr}: Block@{val.start_offset}")
                            elif isinstance(val, list) and val and hasattr(val[0], 'start_offset'):
                                print(f"    {attr}: {[b.start_offset for b in val]}")
                            else:
                                print(f"    {attr}: {val}")
                    except:
                        pass

# Find the TRY_EXCEPT region
for region in analyzer.regions:
    if isinstance(region, TryExceptRegion):
        print(f"\n=== TRY_EXCEPT region ===")
        print(f"  entry: {region.entry.start_offset if region.entry else None}")
        print(f"  try_blocks: {[b.start_offset for b in region.try_blocks]}")
        print(f"  handler_entry_blocks: {[b.start_offset for b in region.handler_entry_blocks]}")
        print(f"  except_handlers:")
        for exc_type, exc_name, handler_blocks in region.except_handlers:
            print(f"    ({exc_type}, {exc_name}): {[b.start_offset for b in handler_blocks]}")
        break
