#!/usr/bin/env python
"""R36 fix: Skip children whose entry is in else_blocks when processing then branch."""

import sys

filepath = 'core/cfg/region_ast_generator.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = (
    "            child_reachable_from_then = self._is_child_reachable_from_blocks(child, region.then_blocks)\n"
    "            if not child_reachable_from_then:\n"
    "                then_offset_min = min((b.start_offset for b in region.then_blocks), default=None)\n"
    "                then_offset_max = max((b.start_offset for b in region.then_blocks), default=None)\n"
    "                if then_offset_min is not None and then_offset_max is not None:\n"
    "                    child_block_offsets = {b.start_offset for b in child.blocks}\n"
    "                    has_overlap = any(\n"
    "                        then_offset_min <= bo <= then_offset_max\n"
    "                        for bo in child_block_offsets\n"
    "                    )\n"
    "                    if has_overlap:\n"
    "                        child_reachable_from_then = True\n"
    "            if child_reachable_from_then:\n"
)

new = (
    "            # [R36 fix] _is_child_reachable_from_blocks may follow back edges\n"
    "            # (JUMP_BACKWARD → loop header → if condition → else entry), giving\n"
    "            # a false positive for children in the else branch. Explicitly\n"
    "            # exclude children whose entry is in else_blocks.\n"
    "            if region.else_blocks and child.entry in set(region.else_blocks):\n"
    "                child_reachable_from_then = False\n"
    "            else:\n"
    "                child_reachable_from_then = self._is_child_reachable_from_blocks(child, region.then_blocks)\n"
    "                if not child_reachable_from_then:\n"
    "                    then_offset_min = min((b.start_offset for b in region.then_blocks), default=None)\n"
    "                    then_offset_max = max((b.start_offset for b in region.then_blocks), default=None)\n"
    "                    if then_offset_min is not None and then_offset_max is not None:\n"
    "                        child_block_offsets = {b.start_offset for b in child.blocks}\n"
    "                        has_overlap = any(\n"
    "                            then_offset_min <= bo <= then_offset_max\n"
    "                            for bo in child_block_offsets\n"
    "                        )\n"
    "                        if has_overlap:\n"
    "                            child_reachable_from_then = True\n"
    "            if child_reachable_from_then:\n"
)

if old in content:
    content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: replaced successfully')
else:
    print('ERROR: old string not found')
    sys.exit(1)
