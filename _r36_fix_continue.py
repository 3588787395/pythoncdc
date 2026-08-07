#!/usr/bin/env python
"""R36 fix: Use full block instructions instead of effective_instructions for CONTINUE blocks."""

import sys

filepath = 'core/cfg/region_ast_generator.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# The issue: effective_instructions stops at the first POP_TOP (STATEMENT_TERMINATORS),
# so blocks with multiple expression statements (like two append calls) lose all but
# the first statement. Fix: use full block instructions for CONTINUE processing.
old = (
    "        elif block_role == BlockRole.CONTINUE:\n"
    "            effective = self.region_analyzer.effective_instructions.get(block.start_offset)\n"
    "            if effective:\n"
)

new = (
    "        elif block_role == BlockRole.CONTINUE:\n"
    "            # [R36 fix] Use full block instructions instead of effective_instructions.\n"
    "            # effective_instructions stops at the first POP_TOP (STATEMENT_TERMINATORS),\n"
    "            # so blocks with multiple expression statements (e.g. two append calls\n"
    "            # followed by JUMP_BACKWARD) lose all but the first statement.\n"
    "            effective = [i for i in block.instructions\n"
    "                         if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',\n"
    "                                             'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',\n"
    "                                             'JUMP_FORWARD', 'JUMP_ABSOLUTE')]\n"
    "            if effective:\n"
)

if old in content:
    content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: replaced successfully')
else:
    print('ERROR: old string not found')
    sys.exit(1)
