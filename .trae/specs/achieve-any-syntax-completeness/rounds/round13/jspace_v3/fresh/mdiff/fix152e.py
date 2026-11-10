# fix152e.py: [v152-DUALUNPACK2] chained tuple-unpack in the while-prefix extractor
#   `(fromline, fromtext), (toline, totext) = fromdata, todata` at a while's
#   condition_block prefix compiles LOAD x; LOAD y; SWAP 2; UNPACK 2; STORE a;
#   STORE b; UNPACK 2; STORE c; STORE d. The state machine reconstructs the
#   first unpack's value = TOS(fromdata) but drops the residual stack element
#   (todata): the second UNPACK sees an empty buffer -> value None -> its
#   targets are silently dropped (toline/totext become LOAD_GLOBAL —
#   difflib.HtmlDiff._line_wrapper real shape, judge "Different bytecode").
#   Fix: (1) after a buffer-backed reconstruct, capture the residual stack
#   (non-PUSH_NULL elements below TOS, TOS-first) as pending values; an
#   immediately-following UNPACK with an empty buffer pops its value from the
#   pending list. (2) when the first unpack's completion is directly followed
#   by another UNPACK, hold its (target, value) and — if the chained unpack's
#   value came from the residual — emit the COMBINED Assign
#   targets=[Tuple([held_target, chain_target])], value=Tuple([held_value,
#   chain_value]) (source order), which recompiles byte-identical via the same
#   SWAP+multi-UNPACK shape. Independent consecutive unpacks (own buffers) and
#   any mismatch fall back to the existing per-unpack emission (C3).
import io

p = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
s = io.open(p, encoding='utf-8-sig').read()

# --- anchor 1: state init ---
a1 = """            pre_stmts: List[Dict[str, Any]] = []
            _eps_instrs: List[Instruction] = []
            _eps_unpack_info = None
            _eps_import_skip_remaining = 0"""
assert a1 in s, 'a1 missing'
r1 = """            pre_stmts: List[Dict[str, Any]] = []
            _eps_instrs: List[Instruction] = []
            _eps_unpack_info = None
            # [v152-DUALUNPACK2] 链式解包残栈值队列 + 合并发射持存
            # （difflib._line_wrapper `(fromline, fromtext), (toline, totext) =
            # fromdata, todata` 实形——首解包值=栈顶，残栈元素是后续解包的
            # 值源；独立连续解包各有自己的值缓冲，不落本路径）。
            _v152_dual_pending: List[Dict[str, Any]] = []
            _v152_chain_holds: List[tuple] = []
            _eps_import_skip_remaining = 0"""
s = s.replace(a1, r1, 1)

# --- anchor 2: UNPACK_SEQUENCE branch ---
a2 = """                    if _instr.opname == 'UNPACK_SEQUENCE':
                        _val_instrs = [i for i in _eps_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        _val = self.expr_reconstructor.reconstruct(_val_instrs) if _val_instrs else None
                        _eps_unpack_info = {'value': _val, 'targets': [], 'count': _instr.arg}
                        _eps_instrs = []
                        continue
                    if _instr.opname == 'UNPACK_EX':
                        _val_instrs = [i for i in _eps_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        _val = self.expr_reconstructor.reconstruct(_val_instrs) if _val_instrs else None"""
assert a2 in s, 'a2 missing'
r2 = """                    if _instr.opname == 'UNPACK_SEQUENCE':
                        _val_instrs = [i for i in _eps_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        # [v152-DUALUNPACK2] 值源：本解包有自己的值缓冲时走
                        # 既有 reconstruct（并捕获残栈为后续解包的 pending 值
                        # 队列，TOS 在前）；缓冲为空且紧邻前一个解包留下残栈
                        # 时从队列取值（链式解包的次级值源=残栈元素）。
                        if _val_instrs:
                            _val = self.expr_reconstructor.reconstruct(_val_instrs)
                            _v152_nn = [sx for sx in self.expr_reconstructor.stack
                                        if not (isinstance(sx, dict) and sx.get('type') == 'PUSH_NULL')]
                            _v152_dual_pending = list(reversed(_v152_nn[:-1])) if len(_v152_nn) >= 2 else []
                            _v152_from_residual = False
                        elif _v152_dual_pending:
                            _val = _v152_dual_pending.pop(0)
                            _v152_from_residual = True
                        else:
                            _val = None
                            _v152_from_residual = False
                        _eps_unpack_info = {'value': _val, 'targets': [], 'count': _instr.arg,
                                            '_v152_from_residual': _v152_from_residual}
                        _eps_instrs = []
                        continue
                    if _instr.opname == 'UNPACK_EX':
                        _val_instrs = [i for i in _eps_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        if _val_instrs:
                            _val = self.expr_reconstructor.reconstruct(_val_instrs)
                            _v152_nn = [sx for sx in self.expr_reconstructor.stack
                                        if not (isinstance(sx, dict) and sx.get('type') == 'PUSH_NULL')]
                            _v152_dual_pending = list(reversed(_v152_nn[:-1])) if len(_v152_nn) >= 2 else []
                            _v152_from_residual = False
                        elif _v152_dual_pending:
                            _val = _v152_dual_pending.pop(0)
                            _v152_from_residual = True
                        else:
                            _val = None
                            _v152_from_residual = False"""
s = s.replace(a2, r2, 1)

# --- anchor 3: completion branch ---
a3 = """                            if len(_eps_unpack_info['targets']) == _eps_unpack_info['count']:
                                _target = {
                                    'type': 'Tuple',
                                    'elts': _eps_unpack_info['targets'],
                                    'ctx': 'Store',
                                }
                                if _eps_unpack_info['value']:
                                    pre_stmts.append({'type': 'Assign', 'targets': [_target], 'value': _eps_unpack_info['value']})
                                _eps_unpack_info = None"""
assert a3 in s, 'a3 missing'
r3 = """                            if len(_eps_unpack_info['targets']) == _eps_unpack_info['count']:
                                _target = {
                                    'type': 'Tuple',
                                    'elts': _eps_unpack_info['targets'],
                                    'ctx': 'Store',
                                }
                                if _eps_unpack_info['value']:
                                    # [v152-DUALUNPACK2] 链式解包合并发射：本解包
                                    # 完成处后随指令直接是 UNPACK_* 且本解包值来自
                                    # 残栈时，与持存的首解包合并为单条 Assign
                                    # （targets=[Tuple([首对, 链对...])]、
                                    # value=Tuple([首值, 链值...])源级元组序）——
                                    # 重编译经同一 SWAP+多 UNPACK 形再生（字节等
                                    # 价）。独立连续解包（各自值缓冲）逐位落回既有
                                    # 逐解包发射。
                                    _v152_ni = -1
                                    try:
                                        _v152_ni = cond_block.instructions.index(_instr) + 1
                                    except (ValueError, AttributeError):
                                        _v152_ni = -1
                                    _v152_next = (cond_block.instructions[_v152_ni]
                                                  if 0 <= _v152_ni < len(cond_block.instructions) else None)
                                    if (not _eps_unpack_info.get('_v152_from_residual')
                                            and _v152_next is not None
                                            and _v152_next.opname in ('UNPACK_SEQUENCE', 'UNPACK_EX')):
                                        _v152_chain_holds.append((_target, _eps_unpack_info['value']))
                                        _eps_unpack_info = None
                                        _eps_instrs = []
                                        continue
                                    if _eps_unpack_info.get('_v152_from_residual') and _v152_chain_holds:
                                        _h_target, _h_value = _v152_chain_holds.pop()
                                        pre_stmts.append({
                                            'type': 'Assign',
                                            'targets': [{'type': 'Tuple',
                                                         'elts': [_h_target, _target],
                                                         'ctx': 'Store'}],
                                            'value': {'type': 'Tuple',
                                                      'elts': [_h_value, _eps_unpack_info['value']],
                                                      'ctx': 'Load'},
                                        })
                                        _eps_unpack_info = None
                                        _eps_instrs = []
                                        continue
                                    pre_stmts.append({'type': 'Assign', 'targets': [_target], 'value': _eps_unpack_info['value']})
                                _eps_unpack_info = None"""
s = s.replace(a3, r3, 1)

io.open(p, 'w', encoding='utf-8-sig').write(s)
print('fix E inserted')

import py_compile
py_compile.compile(p, doraise=True)
print('syntax OK')
