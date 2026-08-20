#!/usr/bin/env python3
"""Inline trace: directly patch the for loop in _process_if_blocks"""

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

# Read the source file to find the exact location of the for loop
with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line "for block in sorted(blocks, key=lambda b: b.start_offset):"
for i, line in enumerate(lines):
    if 'for block in sorted(blocks' in line:
        print(f"Found for loop at line {i+1}: {line.strip()}")
        # Show context
        for j in range(max(0,i-2), min(len(lines), i+5)):
            print(f"  {j+1}: {lines[j].rstrip()}")
        break