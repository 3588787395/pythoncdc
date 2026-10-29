# Apply er-earlyret polarity fix (rr-v5r89) via exact line-slice replacement.
import sys

P = r'F:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py'
raw = open(P, 'rb').read().decode('utf-8')
assert '\r\n' in raw and raw.replace('\r\n', '').count('\n') == 0
src = raw.replace('\r\n', '\n')
lines = src.split('\n')

# locate the elif LOAD_CONST line (0-based) inside 12600..12760 region
idx = None
for k in range(12600, 12760):
    if "elif _br_instrs and _br_instrs[0].opname == 'LOAD_CONST' and _br_instrs[0].argval is not None:" in lines[k]:
        idx = k
        break
assert idx is not None, 'anchor not found'
# sanity: next lines
assert lines[idx + 1].strip() == 'if not _is_module:', lines[idx + 1]
assert lines[idx + 2].strip() == "_return_val = {'type': 'Constant', 'value': _br_instrs[0].argval}", lines[idx + 2]
assert 'if _return_val is not None:' in lines[idx + 3], lines[idx + 3]

NEW = """                                    elif _br_instrs and _br_instrs[0].opname == 'LOAD_CONST' and _br_instrs[0].argval is not None:
                                        if not _is_module:
                                            _return_val = {'type': 'Constant', 'value': _br_instrs[0].argval}
                                    elif (_br_instrs and _br_instrs[0].opname == 'LOAD_CONST'
                                          and _br_instrs[0].argval is None
                                          and not _is_module
                                          and _break_or_return_block is not None
                                          and any(i.opname in ('RETURN_VALUE', 'RETURN_CONST')
                                                  for i in _break_or_return_block.instructions)):
                                        # [er-NONE-V5R89] `LOAD_CONST None; RETURN_VALUE` 臂只可能
                                        # 是真实 `return None`（break 在字节码中是 JUMP_FORWARD，不含
                                        # RETURN_VALUE）——旧路径因 argval is None 不回收返回值而把该
                                        # 臂降级发射为 Break（er3：`if not items: return None` 反编译
                                        # 为 `if items: break`，极性与语义双错）。臂块按 RETURN/
                                        # RETURN_NONE 角色被选中（上方 role 判据），此处仅补齐
                                        # Constant(None) 返回值；模块级仍不发射 return（旧守卫保留）。
                                        _return_val = {'type': 'Constant', 'value': None}
                                # [er-POL-V5R89] 条件跳转极性：本手写路径把 return/break 臂当
                                # then 分支发射 `if test: <臂>`，但臂可能在条件为**假**时执行
                                # （CPython 3.11 对 `if not cond: <臂>` 做跳转翻转：编译为
                                # `LOAD cond; POP_JUMP_IF_TRUE(跳过臂)`）——旧路径不看跳转
                                # 极性，er3/er4（REAL46-003 _c3_merge 早返回守卫）实测把
                                # `if not items: return` 真反转为 `if items: return/break`
                                # （语义错误）。判据（结构事实，无名字/偏移特例）：条件跳转
                                # 指令 argval 即跳转目标块偏移——臂块偏移 == 跳转目标 ⟶ 臂在
                                # test 为真时执行（不反转），否则臂在 test 为假时执行（臂前加
                                # Not）。仅对 POP_JUMP_FORWARD/BACKWARD_IF_TRUE/IF_FALSE 判定，
                                # 其余跳转形态维持旧行为（C3）。
                                _er_jump_op = jump_instr.opname if jump_instr is not None else ''
                                if (_er_jump_op in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                                    'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')
                                        and _break_or_return_block is not None
                                        and getattr(jump_instr, 'argval', None) is not None):
                                    _er_ret_on_true = ((_er_jump_op.endswith('IF_TRUE')) ==
                                                       (jump_instr.argval == _break_or_return_block.start_offset))
                                    if not _er_ret_on_true:
                                        test_expr = {'type': 'UnaryOp', 'op': 'Not', 'operand': test_expr}
                                if _return_val is not None:"""

# replace lines idx..idx+3 (4 lines) with NEW
old_seg = '\n'.join(lines[idx:idx + 4])
assert lines[idx + 3].strip() == 'if _return_val is not None:', lines[idx + 3]
lines[idx:idx + 4] = NEW.split('\n')
out = '\n'.join(lines)
open(P, 'wb').write(out.replace('\n', '\r\n').encode('utf-8'))
print('applied at line', idx + 1, 'delta lines:', len(NEW.split('\n')) - 4)
