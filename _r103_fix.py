#!/usr/bin/env python3
"""修复 _efe_is_continue_only 逻辑"""
import os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core', 'cfg', 'region_ast_generator.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = """                    if not _efe_is_continue_only:
                        final_else_stmts = self._process_if_blocks(region.elif_final_else, region, branch='else')
                        if not self._r23n16_blocks_have_explicit_return(region.elif_final_else):
                            while (final_else_stmts and
                                   isinstance(final_else_stmts[-1], dict) and
                                   final_else_stmts[-1].get('type') == 'Return' and
                                   isinstance(final_else_stmts[-1].get('value'), dict) and
                                   final_else_stmts[-1]['value'].get('type') == 'Constant' and
                                   final_else_stmts[-1]['value'].get('value') is None):
                                final_else_stmts.pop()
                        if final_else_stmts:
                            nested_elif_stmts[0]['orelse'] = final_else_stmts
        final_else_stmts = None
        if not nested_elif_stmts and region.elif_final_else:"""

new = """                    if _efe_is_continue_only:
                        for _fe_b in region.elif_final_else:
                            self.generated_blocks.add(_fe_b)
                        nested_elif_stmts[0]['orelse'] = [{'type': 'Continue'}]
                    else:
                        final_else_stmts = self._process_if_blocks(region.elif_final_else, region, branch='else')
                        if not self._r23n16_blocks_have_explicit_return(region.elif_final_else):
                            while (final_else_stmts and
                                   isinstance(final_else_stmts[-1], dict) and
                                   final_else_stmts[-1].get('type') == 'Return' and
                                   isinstance(final_else_stmts[-1].get('value'), dict) and
                                   final_else_stmts[-1]['value'].get('type') == 'Constant' and
                                   final_else_stmts[-1]['value'].get('value') is None):
                                final_else_stmts.pop()
                        if final_else_stmts:
                            nested_elif_stmts[0]['orelse'] = final_else_stmts
                        final_else_stmts = None
        if not nested_elif_stmts and region.elif_final_else:"""

count = content.count(old)
print(f'Found {count} matches')
if count == 1:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Replaced successfully')
else:
    print('Skipping: multiple or no matches')
