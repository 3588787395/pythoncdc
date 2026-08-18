#!/usr/bin/env python3
"""回退 LOOP_BACK_EDGE 修改"""
import os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core', 'cfg', 'region_ast_generator.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old1 = "self.region_analyzer.get_block_role(b) in (BlockRole.PURE_CONTINUE, BlockRole.CONTINUE, BlockRole.LOOP_BACK_EDGE)"
new1 = "self.region_analyzer.get_block_role(b) in (BlockRole.PURE_CONTINUE, BlockRole.CONTINUE)"

count = content.count(old1)
print(f'Found {count} matches for old1')
if count > 0:
    content = content.replace(old1, new1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Reverted {count} occurrences')
else:
    print('No matches found')
