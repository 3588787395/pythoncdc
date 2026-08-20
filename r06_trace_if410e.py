#!/usr/bin/env python3
"""Trace _loop_dispatch_block for block@410"""

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

# Monkey-patch _loop_dispatch_block
_orig = RegionASTGenerator._loop_dispatch_block
def traced(self, block, region, child_info, boolop_for_while,
           body_stmts, body_blocks_no_header, back_edge_stmts,
           natural_back_edge, back_edge_source_blocks):
    is_target = block.start_offset == 410

    if is_target:
        print(f"\n=== _loop_dispatch_block @410 ===")
        print(f"  role: {self.region_analyzer.get_block_role(block)}")
        print(f"  successors: {[s.start_offset for s in block.successors]}")
        for s in block.successors:
            print(f"    succ @{s.start_offset}: role={self.region_analyzer.get_block_role(s)}")
        # Check if block is entry of any region
        er = self.region_analyzer.get_entry_region_for_block(block)
        print(f"  entry_region: {type(er).__name__ if er else None}")
        if er and isinstance(er, IfRegion):
            print(f"    IfRegion type={er.region_type}")
            print(f"    then_blocks={[b.start_offset for b in er.then_blocks]}")
            print(f"    else_blocks={[b.start_offset for b in (er.else_blocks or [])]}")
            print(f"    merge_block={er.merge_block.start_offset if er.merge_block else None}")

    result = _orig(self, block, region, child_info, boolop_for_while,
                   body_stmts, body_blocks_no_header, back_edge_stmts,
                   natural_back_edge, back_edge_source_blocks)

    if is_target:
        print(f"  After: handled={result}")
        print(f"  body_stmts: {[s.get('type','?') if isinstance(s,dict) else type(s).__name__ for s in body_stmts]}")
        print(f"  body_blocks_no_header: {[b.start_offset for b in body_blocks_no_header]}")
        print(f"  448: {448 in self.generated_offsets}, 488: {488 in self.generated_offsets}")

    return result

RegionASTGenerator._loop_dispatch_block = traced

gen = RegionASTGenerator(cfg, recursive=True, parent_code=orig_co)
result = gen.generate()

print(f"\n=== Final ===")
print(f"Generated offsets: {sorted(gen.generated_offsets)}")
print(f"448: {448 in gen.generated_offsets}, 488: {488 in gen.generated_offsets}")