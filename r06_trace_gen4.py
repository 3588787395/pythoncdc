#!/usr/bin/env python3
"""Trace where block@410 gets marked as generated before _process_if_blocks"""

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

# Monkey-patch generated_blocks.add to trace when block@410 is added
_orig_add = None

class TracedSet(set):
    def add(self, item):
        if hasattr(item, 'start_offset') and item.start_offset == 410:
            import traceback
            print(f"\n*** Block@410 added to generated_blocks ***")
            traceback.print_stack()
        super().add(item)

gen = RegionASTGenerator(cfg, recursive=True, parent_code=orig_co)
gen.generated_blocks = TracedSet(gen.generated_blocks)

result = gen.generate()

print(f"\n=== Final ===")
print(f"448: {448 in gen.generated_offsets}, 488: {488 in gen.generated_offsets}")