#!/usr/bin/env python3
"""Apply R45 fix to region_ast_generator.py"""
import re

filepath = "core/cfg/region_ast_generator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the exact block to replace
old_block = """                        elif stmt_instrs:
                            stmt = self._build_statement(stmt_instrs)
                            if stmt:
                                stmts.append(stmt)
                        stmt_instrs = []
                        skip_initial_pop = True
                        for ri in remaining_after:
                            if ri.opname in ('LOAD_CONST', 'STORE_FAST', 'STORE_NAME',
                                           'STORE_GLOBAL', 'STORE_DEREF', 'DELETE_FAST',
                                           'DELETE_NAME', 'DELETE_GLOBAL', 'DELETE_DEREF'):
                                skip_offsets.add(ri.offset)
                            elif ri.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
                                             'JUMP_BACKWARD_NO_INTERRUPT', 'RETURN_VALUE', 'RETURN_CONST'):
                                skip_offsets.add(ri.offset)
                                break
                            else:
                                break
                        continue"""

new_block = """                        elif _has_return_after_cleanup and not stmt_instrs:
                            # [R45 fix] Return value comes AFTER as-var cleanup
                            # chain. Collect instructions between cleanup end (r2)
                            # and RETURN_VALUE as the return value expression.
                            # Algorithm basis: Principle 2 (unique ownership) -
                            # return value expression belongs to Return statement,
                            # as-var cleanup belongs to except mechanism framework.
                            _cleanup_end_idx = remaining.index(r2) + 1
                            _return_value_instrs = [
                                ri for ri in remaining[_cleanup_end_idx:]
                                if ri.opname not in ('RETURN_VALUE', 'RETURN_CONST',
                                                     'RESUME', 'NOP', 'CACHE',
                                                     'PUSH_NULL', 'EXTENDED_ARG')]
                            if _return_value_instrs:
                                _ret_expr = self.expr_reconstructor.reconstruct(
                                    _return_value_instrs)
                                if _ret_expr is not None:
                                    stmts.append({'type': 'Return', 'value': _ret_expr})
                                elif (len(_return_value_instrs) == 1
                                      and _return_value_instrs[0].opname == 'LOAD_CONST'):
                                    stmts.append({'type': 'Return', 'value': {
                                        'type': 'Constant',
                                        'value': _return_value_instrs[0].argval}})
                                else:
                                    stmt = self._build_statement(_return_value_instrs)
                                    if stmt:
                                        stmts.append(stmt)
                            else:
                                stmts.append({'type': 'Return', 'value': None})
                        elif stmt_instrs:
                            stmt = self._build_statement(stmt_instrs)
                            if stmt:
                                stmts.append(stmt)
                        stmt_instrs = []
                        skip_initial_pop = True
                        # [R45 fix] Only skip the as-var cleanup chain (r0, r1,
                        # r2) and RETURN_VALUE, NOT any LOAD_CONST between them
                        # that forms the return value expression. Old code
                        # unconditionally skipped ALL LOAD_CONST after POP_EXCEPT,
                        # erasing return values (e.g. `return 0` -> `return None`).
                        skip_offsets.add(r0.offset)
                        skip_offsets.add(r1.offset)
                        skip_offsets.add(r2.offset)
                        _after_cleanup_r45 = remaining[remaining.index(r2) + 1:]
                        for ri in _after_cleanup_r45:
                            if ri.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                                skip_offsets.add(ri.offset)
                                break
                            elif ri.opname in ('RESUME', 'NOP', 'CACHE',
                                               'PUSH_NULL', 'EXTENDED_ARG'):
                                skip_offsets.add(ri.offset)
                            else:
                                break
                        continue"""

if old_block in content:
    content = content.replace(old_block, new_block, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: R45 fix applied")
else:
    # Try to find the block with flexible whitespace
    lines = content.split('\n')
    # Find the line "                        elif stmt_instrs:" at the right indentation
    for i, line in enumerate(lines):
        if 'elif stmt_instrs:' in line and i > 17870 and i < 17890:
            print(f"Found 'elif stmt_instrs:' at line {i+1}: {repr(line)}")
    # Find the skip_offsets loop
    for i, line in enumerate(lines):
        if 'for ri in remaining_after:' in line and i > 17880 and i < 17900:
            print(f"Found 'for ri in remaining_after:' at line {i+1}: {repr(line)}")
    print("FAILED: old_block not found exactly")
    # Print the actual content around line 17880
    for i in range(17878, 17898):
        print(f"  {i+1}: {repr(lines[i])}")
