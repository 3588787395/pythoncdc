#!/usr/bin/env python3
"""Round 5 fix: prevent condition negation for continue/break in exit successor handling"""

import shutil

file_path = "core/cfg/region_ast_generator.py"
shutil.copy2(file_path, file_path + ".r05_backup")

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: In _loop_handle_exit_successors, when jump is to continue,
# don't negate the condition - generate full if/else instead
old_code_1 = """                    if _is_jump_to_break and not _is_if_false:
                        # jump_if_true to break: "条件True→break", 需要取反为"条件Not→body"
                        _negate = True
                    elif _is_jump_to_break and _is_if_false:
                        # jump_if_false to break: "条件False→break", 即"条件True→body", 不取反
                        _negate = False
                    elif _is_jump_to_continue:
                        # jump to loop header (continue): 保持原有取反逻辑
                        _negate = _is_if_false
                    elif _jumps_inside:
                        _negate = not _is_if_false
                    else:
                        _negate = _is_if_false
                    _cond_expr = _negate_expr(_expr) if _negate else _expr
                    if _is_jump_to_continue:
                        _hdr_stmts.append({'type': 'If', 'test': _cond_expr, 'body': [{'type': 'Continue'}]})
                    else:
                        _hdr_stmts.append({'type': 'If', 'test': _cond_expr, 'body': [{'type': 'Break'}]})"""

new_code_1 = """                    if _is_jump_to_break and not _is_if_false:
                        _negate = True
                        _cond_expr = _negate_expr(_expr) if _negate else _expr
                        _hdr_stmts.append({'type': 'If', 'test': _cond_expr, 'body': [{'type': 'Break'}]})
                    elif _is_jump_to_break and _is_if_false:
                        _negate = False
                        _cond_expr = _negate_expr(_expr) if _negate else _expr
                        _hdr_stmts.append({'type': 'If', 'test': _cond_expr, 'body': [{'type': 'Break'}]})
                    elif _is_jump_to_continue:
                        if _is_if_false:
                            _then_succ = _fall_through
                            _else_succ = _jump_block
                        else:
                            _then_succ = _jump_block
                            _else_succ = _fall_through
                        _then_stmts_full = self._generate_block_statements(_then_succ) if _then_succ else []
                        if not _then_stmts_full:
                            _then_stmts_full = [{'type': 'Pass'}]
                        self.generated_blocks.add(_then_succ)
                        self.generated_offsets.add(_then_succ.start_offset)
                        self.generated_blocks.add(_else_succ)
                        self.generated_offsets.add(_else_succ.start_offset)
                        _hdr_stmts.append({'type': 'If', 'test': _expr,
                                           'body': _then_stmts_full,
                                           'orelse': [{'type': 'Continue'}]})
                    elif _jumps_inside:
                        _negate = not _is_if_false
                        _cond_expr = _negate_expr(_expr) if _negate else _expr
                        _hdr_stmts.append({'type': 'If', 'test': _cond_expr, 'body': [{'type': 'Break'}]})
                    else:
                        _negate = _is_if_false
                        _cond_expr = _negate_expr(_expr) if _negate else _expr
                        _hdr_stmts.append({'type': 'If', 'test': _cond_expr, 'body': [{'type': 'Break'}]})"""

if old_code_1 in content:
    content = content.replace(old_code_1, new_code_1, 1)
    print("Fix 1 applied: continue handling in _loop_handle_exit_successors")
else:
    print("ERROR: Fix 1 target not found!")

# Fix 2: Also fix the return negation in line 7418
old_code_2 = """                elif _block_succ_return and not _block_succ_break and not [_s for s in _exit_succs if s not in _block_succ_return]:
                    _negate = (not _is_if_false) if _jumps_inside else _is_if_false
                    _cond_expr = _negate_expr(_expr) if _negate else _expr
                    _return_block = _block_succ_return[0]
                    _return_role = self.region_analyzer.get_block_role(_return_block)
                    if _return_role in (BlockRole.RETURN, BlockRole.RETURN_NONE):
                        _ret_ast = self._generate_return_ast(_return_block)
                        _return_stmts = [_ret_ast] if _ret_ast else [{'type': 'Return', 'value': {'type': 'Constant', 'value': None}}]
                    else:
                        _return_stmts = self._generate_block_statements(_return_block)
                    _return_body = _return_stmts if _return_stmts else [{'type': 'Return', 'value': {'type': 'Constant', 'value': None}}]
                    _hdr_stmts.append({'type': 'If', 'test': _cond_expr, 'body': _return_body})
                    self.generated_blocks.add(_return_block)
                    self.generated_offsets.add(_return_block.start_offset)"""

new_code_2 = """                elif _block_succ_return and not _block_succ_break and not [_s for s in _exit_succs if s not in _block_succ_return]:
                    if _is_if_false:
                        _then_succ = _fall_through
                        _else_succ = _jump_block
                    else:
                        _then_succ = _jump_block
                        _else_succ = _fall_through
                    _return_block = _block_succ_return[0]
                    _return_role = self.region_analyzer.get_block_role(_return_block)
                    if _return_role in (BlockRole.RETURN, BlockRole.RETURN_NONE):
                        _ret_ast = self._generate_return_ast(_return_block)
                        _return_stmts = [_ret_ast] if _ret_ast else [{'type': 'Return', 'value': {'type': 'Constant', 'value': None}}]
                    else:
                        _return_stmts = self._generate_block_statements(_return_block)
                    _return_body = _return_stmts if _return_stmts else [{'type': 'Return', 'value': {'type': 'Constant', 'value': None}}]
                    if _return_block == _then_succ:
                        _hdr_stmts.append({'type': 'If', 'test': _expr, 'body': _return_body})
                    else:
                        _hdr_stmts.append({'type': 'If', 'test': _negate_expr(_expr), 'body': _return_body})
                    self.generated_blocks.add(_return_block)
                    self.generated_offsets.add(_return_block.start_offset)"""

if old_code_2 in content:
    content = content.replace(old_code_2, new_code_2, 1)
    print("Fix 2 applied: return handling in _loop_handle_exit_successors")
else:
    print("ERROR: Fix 2 target not found!")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("All fixes applied!")