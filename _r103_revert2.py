#!/usr/bin/env python3
"""回退第二处修改"""
import os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core', 'cfg', 'region_ast_generator.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = """            _efe_is_continue_only_2 = all(
                (not [i for i in b.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')])
                and any(i.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT') for i in b.instructions)
                for b in region.elif_final_else
            )
            if _efe_is_continue_only_2:
                for _fe_b in region.elif_final_else:
                    self.generated_blocks.add(_fe_b)
                if nested_elif_stmts:
                    nested_elif_stmts[0]['orelse'] = [{'type': 'Continue'}]
                else:
                    nested_elif_stmts = [{'type': 'If', '_is_elif': True, 'test': {'type': 'Constant', 'value': True}, 'body': [{'type': 'Pass'}], 'orelse': [{'type': 'Continue'}]}]
            elif not _efe_is_continue_only_2:"""

new = """            _efe_is_continue_only_2 = all(
                (self.region_analyzer.get_block_role(b) in (BlockRole.PURE_CONTINUE, BlockRole.CONTINUE)
                 and not [i for i in b.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')])
                for b in region.elif_final_else
            )
            if not _efe_is_continue_only_2:"""

count = content.count(old)
print(f'Found {count} matches')
if count == 1:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Reverted successfully')
else:
    print(f'Skipping: {count} matches (expected 1)')
