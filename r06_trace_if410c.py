#!/usr/bin/env python3
"""Trace IfRegion(IF_THEN, entry=410) generation"""

import sys, types
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator, IfRegion
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

# Monkey-patch _if_generate_normal to trace IfRegion@410
_orig_if_normal = RegionASTGenerator._if_generate_normal
def traced_if_normal(self, region):
    if region.entry and region.entry.start_offset == 410:
        print(f"\n=== _if_generate_normal IfRegion@410 ===")
        print(f"  region_type: {region.region_type}")
        print(f"  condition_block: {region.condition_block.start_offset if region.condition_block else None}")
        print(f"  then_blocks: {[b.start_offset for b in region.then_blocks]}")
        print(f"  else_blocks: {[b.start_offset for b in (region.else_blocks or [])]}")
        print(f"  merge_block: {region.merge_block.start_offset if region.merge_block else None}")
        print(f"  blocks: {[b.start_offset for b in region.blocks]}")
        for b in region.then_blocks:
            print(f"  then_block @{b.start_offset} role={self.region_analyzer.get_block_role(b)}")
        if region.merge_block:
            print(f"  merge_block @{region.merge_block.start_offset} role={self.region_analyzer.get_block_role(region.merge_block)}")

    result = _orig_if_normal(self, region)

    if region.entry and region.entry.start_offset == 410:
        print(f"  After: result={result}")
        print(f"  448 generated: {448 in self.generated_offsets}")
        print(f"  488 generated: {488 in self.generated_offsets}")

    return result

RegionASTGenerator._if_generate_normal = traced_if_normal

# Also trace _if_generate_then_branch
_orig_then = RegionASTGenerator._if_generate_then_branch
def traced_then(self, region):
    if region.entry and region.entry.start_offset == 410:
        print(f"\n  --- _if_generate_then_branch IfRegion@410 ---")
        print(f"    then_blocks: {[b.start_offset for b in region.then_blocks]}")

    result = _orig_then(self, region)

    if region.entry and region.entry.start_offset == 410:
        print(f"    result: {result}")
        print(f"    448 generated: {448 in self.generated_offsets}")

    return result

RegionASTGenerator._if_generate_then_branch = traced_then

gen = RegionASTGenerator(cfg, recursive=True, parent_code=orig_co)
result = gen.generate()

print(f"\n=== Final ===")
print(f"Generated offsets: {sorted(gen.generated_offsets)}")
print(f"448 generated: {448 in gen.generated_offsets}")
print(f"488 generated: {488 in gen.generated_offsets}")