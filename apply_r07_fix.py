#!/usr/bin/env python3
"""Round 7 fix: When a BREAK block's successor is a RETURN block (e.g., return False),
generate the return statement instead of break.

Root cause: Block@366 (print + POP_TOP) has its successor as block@406 (return False).
The region analyzer marks block@366 as BREAK because block@406 is outside the loop body.
But block@366 actually contains `print(项为空字符串); return False`, not `print; break`.

Fix: In _process_if_blocks, when processing a BREAK block with meaningful instructions,
check if the block's successor is a RETURN block. If so, generate the block's statements
plus the return statement, instead of break.
"""

import shutil

file_path = "core/cfg/region_ast_generator.py"
shutil.copy2(file_path, file_path + ".r07_backup")

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix: In BREAK block handling, check for RETURN successor
old_code = """            if role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                _meaningful_instrs = [
                    i for i in block.instructions
                    if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                    and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                        'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                    and i.opname not in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                        'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')
                    and i.opname not in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP')
                    and i.opname not in ('RETURN_VALUE', 'RETURN_CONST')
                    and not (i.opname == 'LOAD_CONST' and i.argval is None)
                ]
                if _meaningful_instrs:
                    bs = self._generate_block_statements(block)
                    if bs:
                        stmts.extend(bs)
                    stmts.append({'type': 'Break'})
                    self.generated_blocks.add(block)
                    self.generated_offsets.add(block.start_offset)
                    continue
                stmts.append({'type': 'Break'})
                self.generated_blocks.add(block)
                self.generated_offsets.add(block.start_offset)
                continue"""

new_code = """            if role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                _meaningful_instrs = [
                    i for i in block.instructions
                    if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                    and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                        'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                    and i.opname not in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                        'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')
                    and i.opname not in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP')
                    and i.opname not in ('RETURN_VALUE', 'RETURN_CONST')
                    and not (i.opname == 'LOAD_CONST' and i.argval is None)
                ]
                # [Round 7 fix] Check if the block's successor is a RETURN block.
                # When a block is marked as BREAK but its successor is a return
                # statement (e.g., `return False`), the block actually contains
                # `print(...); return False`, not `print(...); break`.
                _return_succ = None
                for _succ in block.successors:
                    if _succ not in self.generated_blocks:
                        _succ_instrs = [i for i in _succ.instructions
                                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')]
                        if (len(_succ_instrs) <= 2 and
                            any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in _succ_instrs)):
                            _return_succ = _succ
                            break
                if _return_succ is not None and _meaningful_instrs:
                    bs = self._generate_block_statements(block)
                    if bs:
                        stmts.extend(bs)
                    _ret_ast = self._generate_return_ast(_return_succ)
                    if _ret_ast:
                        stmts.append(_ret_ast)
                    else:
                        stmts.append({'type': 'Return', 'value': {'type': 'Constant', 'value': None}})
                    self.generated_blocks.add(block)
                    self.generated_offsets.add(block.start_offset)
                    self.generated_blocks.add(_return_succ)
                    self.generated_offsets.add(_return_succ.start_offset)
                    continue
                if _meaningful_instrs:
                    bs = self._generate_block_statements(block)
                    if bs:
                        stmts.extend(bs)
                    stmts.append({'type': 'Break'})
                    self.generated_blocks.add(block)
                    self.generated_offsets.add(block.start_offset)
                    continue
                stmts.append({'type': 'Break'})
                self.generated_blocks.add(block)
                self.generated_offsets.add(block.start_offset)
                continue"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Round 7 fix applied!")
else:
    print("ERROR: Target not found!")