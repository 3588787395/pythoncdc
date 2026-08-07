#!/usr/bin/env python
"""R36 fix: Exclude GET_ITER-ending blocks from being ternary value blocks."""

import sys

filepath = 'core/cfg/region_analyzer.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add GET_ITER check after the store_or_terminal_ops loop
# GET_ITER is always a for-loop setup instruction, followed by FOR_ITER.
# Its result (iterator) is consumed by FOR_ITER, not by a merge block.
# A block ending with GET_ITER should not be considered a ternary value block.
old = (
    "        for idx, instr in enumerate(effective):\n"
    "            is_last = (idx == len(effective) - 1)\n"
    "            if instr.opname in store_or_terminal_ops:\n"
    "                return False\n"
    "            if instr.opname.startswith('JUMP_') or instr.opname.startswith('POP_JUMP_'):\n"
    "                return False\n"
    "            if not is_last and instr.opname in allowed_terminal_ops:\n"
    "                return False\n"
)

new = (
    "        for idx, instr in enumerate(effective):\n"
    "            is_last = (idx == len(effective) - 1)\n"
    "            if instr.opname in store_or_terminal_ops:\n"
    "                return False\n"
    "            if instr.opname.startswith('JUMP_') or instr.opname.startswith('POP_JUMP_'):\n"
    "                return False\n"
    "            if not is_last and instr.opname in allowed_terminal_ops:\n"
    "                return False\n"
    "        # [R36 fix] GET_ITER is always a for-loop setup instruction,\n"
    "        # immediately followed by FOR_ITER. Its result (iterator) is\n"
    "        # consumed by FOR_ITER, not by a merge block (STORE/RETURN).\n"
    "        # A block ending with GET_ITER is a for-loop setup block, not\n"
    "        # a ternary value block. This prevents if/else with for-loop\n"
    "        # branches from being misidentified as ternary expressions.\n"
    "        if effective and effective[-1].opname == 'GET_ITER':\n"
    "            return False\n"
)

if old in content:
    content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: replaced successfully')
else:
    print('ERROR: old string not found')
    sys.exit(1)
