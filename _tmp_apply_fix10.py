#!/usr/bin/env python3
"""Fix: detect nested try regions by try_offset_range overlap, not just try_blocks membership."""

filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """                is_child = r.parent is region
                is_in_try_blocks = r.entry in set(region.try_blocks)
                is_before_try_start = r.entry.start_offset < region.try_offset_start and r.try_offset_end > region.try_offset_start"""

new = """                is_child = r.parent is region
                is_in_try_blocks = r.entry in set(region.try_blocks)
                # [Round 05 fix] check try_offset_range overlap for nested try detection.
                # When inner try's blocks are already in block_to_region (owned by inner),
                # outer try's try_blocks won't contain them. But their try_offset range
                # still overlaps. This detects nesting even when blocks are uniquely owned.
                is_in_try_offset_range = (region.try_offset_start <= r.try_offset_start
                                          and r.try_offset_end <= region.try_offset_end
                                          and r.try_offset_end - r.try_offset_start
                                          < region.try_offset_end - region.try_offset_start)
                is_before_try_start = r.entry.start_offset < region.try_offset_start and r.try_offset_end > region.try_offset_start"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Edit applied successfully')
else:
    print('ERROR: Old string not found')
