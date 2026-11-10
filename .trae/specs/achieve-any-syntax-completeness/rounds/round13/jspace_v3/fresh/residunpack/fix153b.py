# fix153b.py: [v153-RESIDUNPACK] _ua_unpack_stack machine (generic block body builder)
import io

p = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
s = io.open(p, encoding='utf-8-sig').read()

# init: find the _ua_unpack_stack declaration
a = """                _ua_unpack_stack: List[Dict[str, Any]] = []"""
assert s.count(a) == 1, 'ua init count %d' % s.count(a)
s = s.replace(a, a + """
                # [v153-RESIDUNPACK] 链式解包残栈值队列 + 合并发射持存（兄弟解包链
                # `(a, b), (c, d) = x, y` 的 SWAP 形：首解包值=栈顶、残栈元素是后续
                # 解包值源；嵌套链 `(a, (b, c)) = x` 由既有帧栈归约承担不受影响）。
                _v153_dual_pending: List[Dict[str, Any]] = []
                _v153_chain_holds: List[tuple] = []""", 1)

# unpack branch
a = """                    if _instr.opname == 'UNPACK_SEQUENCE':
                        _ua_vi = [i for i in _ua_stmt_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        _ua_val = self.expr_reconstructor.reconstruct(_ua_vi) if _ua_vi else None
                        _ua_unpack_stack.append({'value': _ua_val, 'targets': [], 'count': _instr.arg})
                        _ua_stmt_instrs = []
                        continue"""
assert a in s, 'ua unpack'
r = """                    if _instr.opname == 'UNPACK_SEQUENCE':
                        _ua_vi = [i for i in _ua_stmt_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        # [v153-RESIDUNPACK] 值源：有值缓冲走既有 reconstruct
                        # （并捕获残栈为 pending 队列，TOS 在前）；空缓冲且紧邻
                        # 前解包留下残栈时从队列取值（兄弟链次级值源=残栈元素；
                        # 嵌套链的子帧值不入发射不受影响）。
                        if _ua_vi:
                            _ua_val = self.expr_reconstructor.reconstruct(_ua_vi)
                            _v153_nn = [sx for sx in self.expr_reconstructor.stack
                                        if not (isinstance(sx, dict) and sx.get('type') == 'PUSH_NULL')]
                            _v153_dual_pending = list(reversed(_v153_nn[:-1])) if len(_v153_nn) >= 2 else []
                            _v153_from_residual = False
                        elif _v153_dual_pending:
                            _ua_val = _v153_dual_pending.pop(0)
                            _v153_from_residual = True
                        else:
                            _ua_val = None
                            _v153_from_residual = False
                        _ua_unpack_stack.append({'value': _ua_val, 'targets': [], 'count': _instr.arg,
                                                 '_v153_from_residual': _v153_from_residual})
                        _ua_stmt_instrs = []
                        continue"""
s = s.replace(a, r, 1)

# completion (top-level emission)
a = """                                if not _ua_unpack_stack:
                                    if _completed['value'] is not None:
                                        _ua_stmts.append({
                                            'type': 'Assign',
                                            'targets': [_completed_tgt],
                                            'value': _completed['value'],
                                        })
                                    break"""
assert a in s, 'ua completion'
r = """                            if not _ua_unpack_stack:
                                    if _completed['value'] is not None:
                                        # [v153-RESIDUNPACK] 顶层帧完成处：本帧值来自
                                        # 残栈且有持存首解包时合并发射（重编译同一
                                        # SWAP+多 UNPACK 形字节等价）；独立连续解包
                                        # 逐位落回既有逐解包发射。
                                        _v153_ni = -1
                                        try:
                                            _v153_ni = block.instructions.index(_instr) + 1
                                        except (ValueError, AttributeError):
                                            _v153_ni = -1
                                        _v153_next = (block.instructions[_v153_ni]
                                                      if 0 <= _v153_ni < len(block.instructions) else None)
                                        if (_completed.get('_v153_from_residual')
                                                and _v153_chain_holds):
                                            _h_target, _h_value = _v153_chain_holds.pop()
                                            _ua_stmts.append({
                                                'type': 'Assign',
                                                'targets': [{'type': 'Tuple',
                                                             'elts': [_h_target, _completed_tgt],
                                                             'ctx': 'Store'}],
                                                'value': {'type': 'Tuple',
                                                          'elts': [_h_value, _completed['value']],
                                                          'ctx': 'Load'},
                                            })
                                            break
                                        _ua_stmts.append({
                                            'type': 'Assign',
                                            'targets': [_completed_tgt],
                                            'value': _completed['value'],
                                        })
                                    _v153_hn = -1
                                    try:
                                        _v153_hn = block.instructions.index(_instr) + 1
                                    except (ValueError, AttributeError):
                                        _v153_hn = -1
                                    _v153_nx = (block.instructions[_v153_hn]
                                                if 0 <= _v153_hn < len(block.instructions) else None)
                                    if (_v153_nx is not None
                                            and _v153_nx.opname in ('UNPACK_SEQUENCE', 'UNPACK_EX')
                                            and _v153_dual_pending):
                                        _v153_chain_holds.append((_completed_tgt, _completed['value']))
                                    break"""
s = s.replace(a, r, 1)
print('machine _ua patched')

io.open(p, 'w', encoding='utf-8-sig').write(s)

import py_compile
py_compile.compile(p, doraise=True)
print('syntax OK')
