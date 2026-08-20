#!/usr/bin/env python3
"""Trace both _generated_regions and _generating_regions for IfRegion@410"""

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

class TracedSet:
    def __init__(self, name, gen_ref):
        self._set = set()
        self._name = name
        self._gen = gen_ref
        self._target_id = None

    def add(self, item):
        if self._target_id is None and hasattr(self._gen, 'regions') and self._gen.regions:
            for r in self._gen.regions:
                if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 410:
                    self._target_id = id(r)
                    break
        if self._target_id is not None and item == self._target_id:
            print(f"\n*** IfRegion@410 id={self._target_id} added to {self._name} ***")
            traceback.print_stack()
        self._set.add(item)

    def discard(self, item):
        if hasattr(self, '_target_id') and self._target_id is not None and item == self._target_id:
            print(f"\n*** IfRegion@410 id={self._target_id} discarded from {self._name} ***")
            traceback.print_stack()
        self._set.discard(item)

    def __contains__(self, item):
        return item in self._set

    def __len__(self):
        return len(self._set)

gen._generated_regions = TracedSet("_generated_regions", gen)
gen._generating_regions = TracedSet("_generating_regions", gen)

result = gen.generate()

print(f"\n=== Final ===")
print(f"448: {448 in gen.generated_offsets}, 488: {488 in gen.generated_offsets}")