#!/usr/bin/env python3
"""Check if block 220 should be split at CONTAINS_OP + POP_JUMP_FORWARD_IF_FALSE"""
import sys, marshal, dis
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
from core.cfg.cfg_builder import CFGBuilder

def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.loads(f.read())

orig_code = load_pyc_code('python_syntax_comprehensive_test.pyc')
for c in orig_code.co_consts:
    if hasattr(c, 'co_code') and c.co_name == 'complex_expressions':
        func_code = c
        break

# Show raw bytecode around offset 220-360
print("=== Raw bytecode 220-380 ===")
for i in dis.get_instructions(func_code):
    if 220 <= i.offset <= 380:
        print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")

# Build CFG and check blocks
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(func_code)
blocks = list(cfg.blocks.values())
print("\n=== CFG blocks 220-380 ===")
for block in sorted(blocks, key=lambda b: b.start_offset):
    if 220 <= block.start_offset <= 380:
        print(f"  Block@{block.start_offset}: succs={[s.start_offset for s in block.successors]}")
        for i in block.instructions:
            print(f"    {i.offset:4d}: {i.opname:30s} {i.argval}")
