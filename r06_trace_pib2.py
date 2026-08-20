#!/usr/bin/env python3
"""Trace what happens inside _process_if_blocks when processing block 410 in elif body"""

import sys, types, json
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

# Monkey-patch _process_if_blocks to trace _nested_if_entry_generate handling
_orig = RegionASTGenerator._process_if_blocks
def traced(self, blocks, region, branch='then'):
    block_offsets = {b.start_offset for b in blocks}
    is_target = 410 in block_offsets or 448 in block_offsets or 488 in block_offsets

    if is_target:
        print(f"\n>>> _process_if_blocks branch={branch}")
        print(f"  blocks: {sorted(block_offsets)}")
        print(f"  region: {type(region).__name__ if region else None} entry={region.entry.start_offset if region and region.entry else None}")
        if region and isinstance(region, IfRegion):
            print(f"  region.then_blocks: {[b.start_offset for b in region.then_blocks]}")
            print(f"  region.else_blocks: {[b.start_offset for b in (region.else_blocks or [])]}")
            print(f"  region.merge_block: {region.merge_block.start_offset if region.merge_block else None}")
        # Check which blocks are already generated
        for b in blocks:
            if b.start_offset in (410, 448, 488):
                print(f"  block @{b.start_offset}: generated={b in self.generated_blocks} role={self.region_analyzer.get_block_role(b)}")

    result = _orig(self, blocks, region, branch)

    if is_target:
        print(f"  After: {len(result) if isinstance(result, list) else 1} stmts")
        for s in (result if isinstance(result, list) else [result]):
            if isinstance(s, dict):
                print(f"  stmt: {s.get('type','?')}")
                if s.get('type') == 'If':
                    test = s.get('test', {})
                    print(f"    test: {test.get('type','?')}")
                    body = s.get('body', [])
                    print(f"    body: {len(body)} stmts")
                    for bs in body:
                        if isinstance(bs, dict):
                            print(f"      {bs.get('type','?')}")
                    orelse = s.get('orelse')
                    if orelse:
                        print(f"    orelse: {len(orelse)} stmts")
                        for es in orelse:
                            if isinstance(es, dict):
                                print(f"      {es.get('type','?')}")
        print(f"  448: {448 in self.generated_offsets}, 488: {488 in self.generated_offsets}")

    return result

RegionASTGenerator._process_if_blocks = traced

# Also trace _generate_region to see what happens when IfRegion@410 is generated
_orig_gen = RegionASTGenerator._generate_region
def traced_gen(self, region):
    is_target = isinstance(region, IfRegion) and region.entry and region.entry.start_offset == 410
    if is_target:
        print(f"\n  *** _generate_region IfRegion@410 ***")
        print(f"    region_id already generated: {id(region) in self._generated_regions}")
        print(f"    region_id generating: {id(region) in self._generating_regions}")
        print(f"    then_blocks: {[b.start_offset for b in region.then_blocks]}")
        print(f"    merge_block: {region.merge_block.start_offset if region.merge_block else None}")

    result = _orig_gen(self, region)

    if is_target:
        print(f"    result: {result}")

    return result

RegionASTGenerator._generate_region = traced_gen

gen = RegionASTGenerator(cfg, recursive=True, parent_code=orig_co)
result = gen.generate()

print(f"\n=== Final ===")
print(f"448: {448 in gen.generated_offsets}, 488: {488 in gen.generated_offsets}")