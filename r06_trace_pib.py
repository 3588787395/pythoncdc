#!/usr/bin/env python3
"""Final trace: patch _process_if_blocks to print exactly what happens with block 410, 448, 488"""

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

# Monkey-patch _process_if_blocks to print each block traversal
_orig = RegionASTGenerator._process_if_blocks
def traced(self, blocks, region, branch='then'):
    # Only trace when blocks contain 410 or 448 or 488
    target_offsets = {410, 448, 488}
    block_offsets = {b.start_offset for b in blocks}
    is_target = bool(target_offsets & block_offsets)

    if is_target:
        print(f"\n>>> _process_if_blocks branch={branch}")
        print(f"  blocks: {sorted(block_offsets)}")
        print(f"  region: {type(region).__name__ if region else None} entry={region.entry.start_offset if region and region.entry else None}")

    # Save original generated_blocks state
    saved_gen = set(self.generated_blocks)

    result = _orig(self, blocks, region, branch)

    if is_target:
        print(f"  After: {len(result) if isinstance(result, list) else 1} stmts")
        new_gen = self.generated_blocks - saved_gen
        new_gen_offsets = {b.start_offset for b in new_gen}
        print(f"  New generated: {sorted(new_gen_offsets)}")
        print(f"  448: {448 in self.generated_offsets}")
        print(f"  488: {488 in self.generated_offsets}")
        for s in (result if isinstance(result, list) else [result]):
            if isinstance(s, dict):
                print(f"  stmt: {s.get('type','?')}")
                if s.get('type') == 'If':
                    body = s.get('body', [])
                    print(f"    body: {len(body)} stmts")
                    for bs in body:
                        if isinstance(bs, dict):
                            print(f"      {bs.get('type','?')}")

    return result

RegionASTGenerator._process_if_blocks = traced

gen = RegionASTGenerator(cfg, recursive=True, parent_code=orig_co)
result = gen.generate()

print(f"\n=== Final ===")
print(f"448: {448 in gen.generated_offsets}, 488: {488 in gen.generated_offsets}")