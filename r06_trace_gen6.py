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

# Patch _generated_regions before calling generate()
# We need to find the target id, but we can't call analyze() separately
# So we'll patch set.add to check for any IfRegion with entry@410

class TracedGeneratedSet(set):
    def __init__(self, gen_ref):
        super().__init__()
        self._gen = gen_ref
        self._target_id = None

    def add(self, item):
        if self._target_id is None and hasattr(self._gen, 'regions'):
            for r in (self._gen.regions or []):
                if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 410:
                    self._target_id = id(r)
                    break
        if self._target_id is not None and item == self._target_id:
            print(f"\n*** IfRegion@410 id={self._target_id} added to _generated_regions ***")
            traceback.print_stack()
        super().add(item)

gen._generated_regions = TracedGeneratedSet(gen)

result = gen.generate()

print(f"\n=== Final ===")
print(f"448: {448 in gen.generated_offsets}, 488: {488 in gen.generated_offsets}")