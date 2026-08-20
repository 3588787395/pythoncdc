"""Apply R8 fix 3: Process RETURN successor after elif_final_else block."""
import re

filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# The exact code to find and modify
old_code = """                stmts.extend(bs)
            self.generated_blocks.add(block)
        return stmts

    def _try_generate_conditional_break"""

new_code = """                stmts.extend(bs)
            self.generated_blocks.add(block)
            # [R8 fix] 区域归约算法原则 2（每块唯一归属）：
            # elif_final_else 中的块（如 `else: print(...); return False`）
            # 的后继如果是 RETURN 块（含 LOAD_CONST+RETURN_VALUE），
            # 需要继续处理该后继块以生成 return 语句。否则 return 语句
            # 丢失或被外层错误归位为 Try 之后的独立 return。
            _block_role = self.region_analyzer.get_block_role(block)
            if _block_role in (BlockRole.TRY_BODY, BlockRole.LOOP_BODY, BlockRole.LOOP_BACK_EDGE):
                for _succ in block.successors:
                    if _succ in self.generated_blocks:
                        continue
                    if any(i.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START') for i in _succ.instructions):
                        continue
                    _succ_role = self.region_analyzer.get_block_role(_succ)
                    _succ_last = _succ.get_last_instruction()
                    if _succ_last and _succ_last.opname == 'RETURN_VALUE':
                        # 后继是 RETURN 块，生成 return 语句
                        _ret_stmts = self._generate_block_statements(_succ)
                        if _ret_stmts:
                            stmts.extend(_ret_stmts)
                        else:
                            _ret_ast = self._generate_return_ast(_succ)
                            if _ret_ast:
                                stmts.append(_ret_ast)
                            else:
                                stmts.append({'type': 'Return', 'value': {'type': 'Constant', 'value': None}})
                        self.generated_blocks.add(_succ)
                        self.generated_offsets.add(_succ.start_offset)
                        break
        return stmts

    def _try_generate_conditional_break"""

if old_code not in content:
    print("ERROR: old_code not found!")
    lines = content.split('\n')
    for i in range(15484, 15500):
        if i < len(lines):
            print(f"  {i+1}: {repr(lines[i])}")
else:
    content = content.replace(old_code, new_code, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix applied successfully!")
