#!/usr/bin/env python3
"""修复 _efe_is_continue_only：改为检查块是否只含 JUMP_BACKWARD 指令"""
import os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core', 'cfg', 'region_ast_generator.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 只修改第一处 _efe_is_continue_only（在 elif_final_else 上下文中）
# 改为检查块是否只含 JUMP_BACKWARD 指令（纯 continue 语义），不依赖 block role
old = """                    _efe_is_continue_only = all(
                        (self.region_analyzer.get_block_role(b) in (BlockRole.PURE_CONTINUE, BlockRole.CONTINUE)
                         and not [i for i in b.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')])
                        for b in region.elif_final_else
                    )
                    if _efe_is_continue_only:"""

new = """                    _efe_is_continue_only = all(
                        (not [i for i in b.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')])
                        and any(i.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT') for i in b.instructions)
                        for b in region.elif_final_else
                    )
                    if _efe_is_continue_only:"""

count = content.count(old)
print(f'Found {count} matches')
if count == 1:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Replaced successfully')
else:
    print(f'Skipping: {count} matches (expected 1)')
