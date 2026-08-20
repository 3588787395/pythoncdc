#!/usr/bin/env python3
"""Trace CFG for validate_data around the problematic blocks"""

import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'core')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
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
print(f"Constants: {[c for c in orig_co.co_consts if not isinstance(c, types.CodeType)]}")
print()

cfg = CFGBuilder().build(orig_co)
blocks = cfg.get_blocks()

# Find blocks around offset 440-530
for block in sorted(blocks, key=lambda b: b.start_offset):
    if block.start_offset >= 380 and block.start_offset <= 540:
        print(f"\nBlock @{block.start_offset}")
        print(f"  End offset: {block.end_offset}")
        print(f"  Successors: {[s.start_offset for s in block.successors]}")
        role = None
        try:
            ra = RegionAnalyzer(cfg)
            ra.analyze()
            role = ra.get_block_role(block)
        except:
            pass
        print(f"  Role: {role}")
        print(f"  Instructions:")
        for instr in block.instructions:
            print(f"    {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")

# Now check region analysis
print("\n=== Region Analysis ===")
ra = RegionAnalyzer(cfg)
ra.analyze()
regions = ra.get_regions()
for region in regions:
    if hasattr(region, 'header_block') and region.header_block:
        print(f"Region header={region.header_block.start_offset}, type={type(region).__name__}")
        if hasattr(region, 'body_blocks'):
            body = [b.start_offset for b in region.body_blocks]
            if any(380 <= b <= 540 for b in body):
                print(f"  Body blocks (filtered): {[b for b in body if 380 <= b <= 540]}")