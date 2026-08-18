#!/usr/bin/env python3
"""修复 _efe_is_continue_only 中的 role 检查，添加 LOOP_BACK_EDGE"""
import os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core', 'cfg', 'region_ast_generator.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修改两处 _efe_is_continue_only 检查
old1 = "self.region_analyzer.get_block_role(b) in (BlockRole.PURE_CONTINUE, BlockRole.CONTINUE)"
new1 = "self.region_analyzer.get_block_role(b) in (BlockRole.PURE_CONTINUE, BlockRole.CONTINUE, BlockRole.LOOP_BACK_EDGE)"

count = content.count(old1)
print(f'Found {count} matches for old1')
if count > 0:
    content = content.replace(old1, new1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Replaced {count} occurrences')
else:
    print('No matches found')
