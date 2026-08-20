#!/usr/bin/env python3
"""Trace where IfRegion@410's id gets added to _generated_regions"""

import sys, types
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator, IfRegion
from core.cfg.region_analyzer import BlockRole
import marshal, traceback

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

gen = RegionASTGenerator(cfg, recursive=True, parent_code=orig_co)

# Find IfRegion@410
ra = gen.region_analyzer
ra.analyze()
target_region = None
for r in ra.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 410:
        target_region = r
        break

if target_region is None:
    print("IfRegion@410 not found!")
    for r in ra.regions:
        if isinstance(r, IfRegion) and r.entry:
            print(f"  IfRegion@{r.entry.start_offset} type={r.region_type}")
else:
    print(f"Found IfRegion@410, id={id(target_region)}")
    print(f"  blocks: {[b.start_offset for b in target_region.blocks]}")
    print(f"  then_blocks: {[b.start_offset for b in target_region.then_blocks]}")
    print(f"  merge_block: {target_region.merge_block.start_offset if target_region.merge_block else None}")

    # Patch _generated_regions.add
    target_id = id(target_region)
    _orig_set = gen._generated_regions
    class TracedGeneratedSet(set):
        def add(self, item):
            if item == target_id:
                print(f"\n*** IfRegion@410 id={target_id} added to _generated_regions ***")
                traceback.print_stack()
            super().add(item)
    gen._generated_regions = TracedGeneratedSet()

    result = gen.generate()

    print(f"\n=== Final ===")
    print(f"448: {448 in gen.generated_offsets}, 488: {488 in gen.generated_offsets}")