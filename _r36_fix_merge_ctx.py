#!/usr/bin/env python
"""R36 fix: Extend value-context chained compare check to handle merge_block
ending with RETURN_VALUE or JUMP_FORWARD (not just SHORT_CIRCUIT_JUMP_OPS)."""

import sys

filepath = 'core/cfg/region_ast_generator.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = (
    "                    if _merge is not None:\n"
    "                        _merge_last = _merge.get_last_instruction()\n"
    "                        if (_merge_last and _merge_last.opname in SHORT_CIRCUIT_JUMP_OPS\n"
    "                                and _merge_last.opname not in ('JUMP_FORWARD',)):\n"
    "                            # merge_block is a BoolOp short-circuit jump block\n"
)

new = (
    "                    if _merge is not None:\n"
    "                        _merge_last = _merge.get_last_instruction()\n"
    "                        # [R36 fix] Extended: chained compare is in value context\n"
    "                        # when merge_block does NOT end with FORWARD_CONDITIONAL_JUMP_OPS\n"
    "                        # (which would indicate an `if` condition). Value-context\n"
    "                        # merge blocks end with SHORT_CIRCUIT_JUMP_OPS (BoolOp operand),\n"
    "                        # RETURN_VALUE (direct return), JUMP_FORWARD (connector), etc.\n"
    "                        if (_merge_last and _merge_last.opname not in FORWARD_CONDITIONAL_JUMP_OPS):\n"
    "                            # merge_block is NOT an if condition — value context\n"
)

if old in content:
    content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: replaced successfully')
else:
    print('ERROR: old string not found')
    sys.exit(1)
