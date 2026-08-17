#!/usr/bin/env python3
"""R92 fix v4: Fix the condition check using start_offset comparison"""
import re

with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the condition: change 'region.merge_block in region.then_blocks' to
# 'any(b.start_offset >= region.merge_block.start_offset for b in region.then_blocks)'
old_cond = "and region.merge_block in region.then_blocks):"
new_cond = "and any(b.start_offset >= region.merge_block.start_offset for b in region.then_blocks)):"

count = content.count(old_cond)
print(f'Found {count} occurrences of old condition')
if count == 1:
    content = content.replace(old_cond, new_cond, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Applied successfully')
else:
    print(f'ERROR: {count} occurrences')
