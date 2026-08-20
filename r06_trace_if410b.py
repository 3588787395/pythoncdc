#!/usr/bin/env python3
"""Trace how block @410 is processed in loop body"""

import sys, types
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import BlockRole, RegionAnalyzer
import marshal

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

cfg = CFGBuilder().build(orig_co)
ra = RegionAnalyzer(cfg, parent_code=orig_co)
ra.analyze()

# Find the LoopRegion
loop_region = None
for r in ra.regions:
    if hasattr(r, 'header_block') and r.header_block and r.header_block.start_offset == 72:
        loop_region = r
        break

if not loop_region:
    print("LoopRegion not found!")
    # List all regions
    for r in ra.regions:
        print(f"  Region: {type(r).__name__} header={getattr(r,'header_block',None)}")
else:
    print(f"LoopRegion header={loop_region.header_block.start_offset}")
    print(f"  body_blocks: {[b.start_offset for b in loop_region.body_blocks]}")
    print(f"  else_blocks: {[b.start_offset for b in (loop_region.else_blocks or [])]}")
    print(f"  children: {[(type(c).__name__, getattr(c,'entry',None) and getattr(c.entry,'start_offset',None)) for c in (loop_region.children or [])]}")

    # Check if block 410 is in body_blocks
    blk410 = cfg.get_block_by_offset(410)
    print(f"\n  Block@410 in body_blocks: {blk410 in loop_region.body_blocks}")
    print(f"  Block@410 in else_blocks: {blk410 in (loop_region.else_blocks or [])}")

    # Check entry region for block 410
    entry_region = ra.get_entry_region_for_block(blk410)
    print(f"  Block@410 entry_region: {entry_region}")
    if entry_region:
        print(f"    type={type(entry_region).__name__}")
        print(f"    entry={getattr(entry_region, 'entry', None) and getattr(entry_region.entry, 'start_offset', None)}")
        print(f"    blocks={[b.start_offset for b in getattr(entry_region, 'blocks', [])]}")

    # Check region for block 410
    region_for_410 = ra.get_region_for_block(blk410)
    print(f"  Block@410 region_for_block: {region_for_410}")
    if region_for_410:
        print(f"    type={type(region_for_410).__name__}")
        print(f"    blocks={[b.start_offset for b in getattr(region_for_410, 'blocks', [])]}")

    # Check if block 410 is a child region entry
    for child in (loop_region.children or []):
        if child.entry is blk410:
            print(f"\n  Block@410 is entry of child {type(child).__name__}")
            if hasattr(child, 'then_blocks'):
                print(f"    then_blocks: {[b.start_offset for b in child.then_blocks]}")
            if hasattr(child, 'else_blocks'):
                print(f"    else_blocks: {[b.start_offset for b in child.else_blocks]}")
            if hasattr(child, 'condition_block'):
                print(f"    condition_block: {getattr(child.condition_block, 'start_offset', None)}")
            break

    # Also check blocks 448 and 488
    for offset in [448, 488]:
        blk = cfg.get_block_by_offset(offset)
        print(f"\n  Block@{offset} role: {ra.get_block_role(blk)}")
        print(f"  Block@{offset} in body_blocks: {blk in loop_region.body_blocks}")
        er = ra.get_entry_region_for_block(blk)
        print(f"  Block@{offset} entry_region: {er}")
        if er:
            print(f"    type={type(er).__name__}")
        r4b = ra.get_region_for_block(blk)
        print(f"  Block@{offset} region_for_block: {r4b}")
        if r4b:
            print(f"    type={type(r4b).__name__}")