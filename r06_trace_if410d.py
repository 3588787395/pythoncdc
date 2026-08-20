#!/usr/bin/env python3
"""Trace _generate_region for IfRegion@410"""

import sys, types
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator, IfRegion, TryExceptRegion, LoopRegion
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

# Monkey-patch _generate_region to trace
_orig_gen = RegionASTGenerator._generate_region
def traced_gen(self, region):
    is_target = hasattr(region, 'entry') and region.entry and region.entry.start_offset == 410
    if is_target:
        print(f"\n=== _generate_region for {type(region).__name__}@410 ===")
        print(f"  region_type: {getattr(region, 'region_type', None)}")

    result = _orig_gen(self, region)

    if is_target:
        print(f"  After: result type={type(result).__name__}")
        if isinstance(result, dict):
            print(f"  result: {result.get('type', '?')}")
        elif isinstance(result, list):
            print(f"  result: [{len(result)} items]")
            for r in result:
                if isinstance(r, dict):
                    print(f"    {r.get('type','?')}")

    return result

RegionASTGenerator._generate_region = traced_gen

gen = RegionASTGenerator(cfg, recursive=True, parent_code=orig_co)
result = gen.generate()

print(f"\n=== Final ===")
print(f"Generated offsets: {sorted(gen.generated_offsets)}")
print(f"448: {448 in gen.generated_offsets}, 488: {488 in gen.generated_offsets}")