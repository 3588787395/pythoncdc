#!/usr/bin/env python3
"""Analyze m075 block structure to understand the if/elif/else pattern."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.cfg.cfg_builder import build_cfg_from_source
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import CONDITIONAL_JUMP_OPS, FORWARD_CONDITIONAL_JUMP_OPS
from core.cfg.code_generator import CodeGenerator

src = 'match x:\n    case 1:\n        if a and b:\n            y = 1\n        elif a or c:\n            y = 2\n        else:\n            y = 3\n    case _:\n        y = 0'

result = build_cfg_from_source(src)
cfg = result[0] if isinstance(result, (list, tuple)) else result

# Analyze the block structure for if/elif/else detection
print("Analyzing block structure for if/elif/else detection:")
for block in cfg.get_blocks_in_order():
    last_instr = block.instructions[-1] if block.instructions else None
    jump_type = None
    jump_target = None
    if last_instr and last_instr.opname in CONDITIONAL_JUMP_OPS:
        jump_type = last_instr.opname
        jump_target = last_instr.argval
    print(f"  Block {block.start_offset}: last_instr={last_instr.opname if last_instr else None}, "
          f"jump_type={jump_type}, jump_target={jump_target}, "
          f"succs={[s.start_offset for s in block.successors]}")
