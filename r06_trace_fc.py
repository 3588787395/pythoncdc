#!/usr/bin/env python3
"""Trace _if_generate_full_elif_chain to find where block@410 gets pre-marked"""

import sys, types
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator, IfRegion
from core.cfg.region_analyzer import BlockRole
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

# Patch _if_generate_full_elif_chain to trace state
_orig = RegionASTGenerator._if_generate_full_elif_chain
def traced(self, region):
    is_target = region.entry and region.entry.start_offset == 76
    if is_target:
        print(f"\n=== _if_generate_full_elif_chain START ===")
        print(f"  410 generated: {410 in self.generated_offsets}")
        print(f"  448 generated: {448 in self.generated_offsets}")
        print(f"  488 generated: {488 in self.generated_offsets}")
        # Check all blocks in region
        for b in region.blocks:
            if b.start_offset in (410, 448, 488):
                print(f"  block @{b.start_offset}: gen={b in self.generated_blocks}")

    result = _orig(self, region)

    if is_target:
        print(f"\n=== _if_generate_full_elif_chain END ===")
        print(f"  410 generated: {410 in self.generated_offsets}")
        print(f"  448 generated: {448 in self.generated_offsets}")
        print(f"  488 generated: {488 in self.generated_offsets}")

    return result

RegionASTGenerator._if_generate_full_elif_chain = traced

# Also patch _if_generate_elif_chain
_orig2 = RegionASTGenerator._if_generate_elif_chain
def traced2(self, region):
    is_target = region.entry and region.entry.start_offset == 76
    if is_target:
        print(f"\n  --- _if_generate_elif_chain START ---")
        print(f"    410 generated: {410 in self.generated_offsets}")
        print(f"    elif_bodies: {[[b.start_offset for b in body] for body in (region.elif_bodies or [])]}")

    result = _orig2(self, region)

    if is_target:
        print(f"    --- _if_generate_elif_chain END ---")
        print(f"    410 generated: {410 in self.generated_offsets}")
        print(f"    448 generated: {448 in self.generated_offsets}")

    return result

RegionASTGenerator._if_generate_elif_chain = traced2

# Also patch _process_if_blocks
_orig3 = RegionASTGenerator._process_if_blocks
def traced3(self, blocks, region, branch='then'):
    block_offsets = {b.start_offset for b in blocks}
    is_target = 410 in block_offsets
    if is_target:
        print(f"\n  >>> _process_if_blocks branch={branch}")
        print(f"    410 generated: {410 in self.generated_offsets}")
        print(f"    blocks: {sorted(block_offsets)}")

    result = _orig3(self, blocks, region, branch)

    if is_target:
        print(f"    After: 448={448 in self.generated_offsets}, 488={488 in self.generated_offsets}")

    return result

RegionASTGenerator._process_if_blocks = traced3

gen = RegionASTGenerator(cfg, recursive=True, parent_code=orig_co)
result = gen.generate()

print(f"\n=== Final ===")
print(f"448: {448 in gen.generated_offsets}, 488: {488 in gen.generated_offsets}")