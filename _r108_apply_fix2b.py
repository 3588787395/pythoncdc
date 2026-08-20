"""Revert fix part 2 and apply corrected version"""
path = r'f:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Revert: remove the dtc-r08 fix part 2
old = """                    # [dtc-r08 fix] 区域归约算法原则 2（每块唯一归属）：
                    # 当 has_finally=True 且 else 块只含返回值表达式加载指令
                    # （不含 STORE/RETURN_VALUE）时，CPython 编译器将 RETURN_VALUE
                    # 放在 finally 正常路径副本块中。else 块的后继是 finally 正常
                    # 路径块（含 finally body + RETURN_VALUE）。依「每块唯一归属」：
                    # else 块的表达式是 return 语句的返回值，而非独立表达式语句。
                    # 检测条件：has_finally=True + else 块不含 RETURN_VALUE/RETURN_CONST
                    # + else 块不含 STORE_* + 后继块含 RETURN_VALUE
                    if region.has_finally:
                        _eb_has_return = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in eb.instructions)
                        _eb_has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_SUBSCR', 'STORE_DEREF', 'STORE_ATTR') for i in eb.instructions)
                        if not _eb_has_return and not _eb_has_store:
                            _ret_succ = None
                            for _succ_eb in eb.successors:
                                if any(i.opname == 'RETURN_VALUE' for i in _succ_eb.instructions):
                                    _ret_succ = _succ_eb
                                    break
                            if _ret_succ is not None:
                                _ret_ebs = self._generate_block_statements(eb)
                                if _ret_ebs and len(_ret_ebs) == 1 and _ret_ebs[0].get('type') == 'Expr':
                                    orelse_stmts.append({'type': 'Return', 'value': _ret_ebs[0]['value']})
                                    self.generated_blocks.add(eb)
                                    self.generated_blocks.add(_ret_succ)
                                    self.generated_offsets.add(eb.start_offset)
                                    self.generated_offsets.add(_ret_succ.start_offset)
                                    continue
                    ebs = self._generate_block_statements(eb)
                    if ebs and _eb_in_loop:"""

new = """                    # [dtc-r08 fix] 区域归约算法原则 2（每块唯一归属）：
                    # 当 has_finally=True 且 else 块只含返回值表达式加载指令
                    # （不含 STORE/RETURN_VALUE）时，CPython 编译器将 RETURN_VALUE
                    # 放在 finally 正常路径副本块中。else 块的后继是 finally 正常
                    # 路径块（含 finally body + RETURN_VALUE）。依「每块唯一归属」：
                    # else 块的表达式是 return 语句的返回值，而非独立表达式语句。
                    # 检测条件：has_finally=True + else 块不含 RETURN_VALUE/RETURN_CONST
                    # + else 块不含 STORE_* + 后继块含 RETURN_VALUE
                    # 注意：不标记后继块为 generated，因为 finally body 部分由
                    # finalbody_stmts 逻辑单独生成。
                    if region.has_finally:
                        _eb_has_return = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in eb.instructions)
                        _eb_has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_SUBSCR', 'STORE_DEREF', 'STORE_ATTR') for i in eb.instructions)
                        if not _eb_has_return and not _eb_has_store:
                            _ret_succ = None
                            for _succ_eb in eb.successors:
                                if any(i.opname == 'RETURN_VALUE' for i in _succ_eb.instructions):
                                    _ret_succ = _succ_eb
                                    break
                            if _ret_succ is not None:
                                _ret_ebs = self._generate_block_statements(eb)
                                if _ret_ebs and len(_ret_ebs) == 1 and _ret_ebs[0].get('type') == 'Expr':
                                    orelse_stmts.append({'type': 'Return', 'value': _ret_ebs[0]['value']})
                                    self.generated_blocks.add(eb)
                                    self.generated_offsets.add(eb.start_offset)
                                    # Mark the return instruction offset as generated
                                    # so _generate_block_statements for the finally
                                    # normal-path block skips the RETURN_VALUE but
                                    # still processes the finally body instructions.
                                    for _ri in _ret_succ.instructions:
                                        if _ri.opname == 'RETURN_VALUE':
                                            self.generated_offsets.add(_ri.offset)
                                    continue
                    ebs = self._generate_block_statements(eb)
                    if ebs and _eb_in_loop:"""

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix part 2 corrected successfully!")
else:
    print("ERROR: Old text not found!")
