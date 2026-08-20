#!/usr/bin/env python3
"""Trace CFG for validate_data around the problematic blocks"""

import sys
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole
import marshal, types, dis

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_all(code, prefix=""):
    name = prefix + code.co_name if prefix else code.co_name
    result = {name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            new_prefix = name + "." if name != "<module>" else ""
            result.update(extract_all(const, new_prefix))
    return result

orig_code = load_code_from_pyc("decompiler_test_comprehensive.cpython-311.pyc")
orig_codes = extract_all(orig_code)

target = "DataProcessor.validate_data"
orig_co = orig_codes[target]

print(f"=== CFG for {target} ===")

cfg = CFGBuilder().build(orig_co)
blocks = cfg.get_blocks_in_order()

# Show blocks around offset 380-540
for block in blocks:
    if block.start_offset >= 380 and block.start_offset <= 540:
        print(f"\nBlock @{block.start_offset}-{block.end_offset}")
        print(f"  Successors: {[s.start_offset for s in block.successors]}")
        print(f"  Instructions:")
        for instr in block.instructions:
            print(f"    {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")

# Now check region analysis
print("\n=== Region Analysis ===")
ra = RegionAnalyzer(cfg)
ra.analyze()

# Show block roles
for block in blocks:
    if block.start_offset >= 380 and block.start_offset <= 540:
        role = ra.get_block_role(block)
        print(f"  Block @{block.start_offset}: role={role}")

# Show regions
regions = ra.get_regions() if hasattr(ra, 'get_regions') else []
if not regions:
    # Try other attributes
    for attr in dir(ra):
        if 'region' in attr.lower() and not attr.startswith('_'):
            val = getattr(ra, attr)
            if val and isinstance(val, (list, dict)):
                print(f"  {attr}: {type(val).__name__} len={len(val)}")
                break

# Also check what regions contain these blocks
for attr in dir(ra):
    if not attr.startswith('_') and 'region' in attr.lower():
        try:
            val = getattr(ra, attr)
            if isinstance(val, list) and len(val) > 0:
                print(f"\n  {attr} ({len(val)} regions):")
                for r in val[:10]:
                    if hasattr(r, 'header_block') and r.header_block:
                        h = r.header_block.start_offset
                        body = [b.start_offset for b in getattr(r, 'body_blocks', [])]
                        print(f"    Region header={h}, body={body}")
        except:
            pass