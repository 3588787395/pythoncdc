#!/usr/bin/env python3
"""Trace block@406's predecessors and role"""

import sys, types
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole
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
ra = RegionAnalyzer(cfg, parent_code=orig_co)
ra.analyze()

blocks = cfg.get_blocks_in_order()

for block in blocks:
    if block.start_offset in (328, 366, 406, 410, 448, 488):
        print(f"\nBlock @{block.start_offset}-{block.end_offset}")
        print(f"  Role: {ra.get_block_role(block)}")
        print(f"  Predecessors: {[p.start_offset for p in block.predecessors]}")
        print(f"  Successors: {[s.start_offset for s in block.successors]}")
        last_i = block.get_last_instruction()
        print(f"  Last instr: {last_i.opname if last_i else None} {last_i.argval if last_i else None}")
        print(f"  Instructions:")
        for instr in block.instructions:
            print(f"    {instr.offset:4d} {instr.opname:30s} {instr.argval}")