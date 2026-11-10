# fix153.py: [v153-RESIDUNPACK] chained tuple-unpack residual-stack family
#   `(a, b), (c, d) = x, y` compiles LOAD x; LOAD y; SWAP 2; UNPACK 2; STORE a;
#   STORE b; UNPACK 2; STORE c; STORE d. Every UNPACK state machine sources the
#   first unpack's value = reconstruct TOS and drops the residual stack element
#   (the chained unpack's value source) -> the second target pair is silently
#   lost, names fall to LOAD_GLOBAL (probe R1-R6 all positions = real R1).
#   Same fix-E pattern per machine: residual pending queue (captured after a
#   buffer-backed reconstruct, non-PUSH_NULL elements below TOS, TOS-first) +
#   empty-buffer UNPACK pops the pending value + completion hold/combined
#   emission (targets=[Tuple([first, chain])], value=Tuple([first_val,
#   chain_val])) when the completion is directly followed by UNPACK_* and the
#   chain unpack's value came from the residual. Independent consecutive
#   unpacks (own buffers) and any mismatch fall back to the existing per-unpack
#   emission bit-for-bit (C3).
import io

p = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
s = io.open(p, encoding='utf-8-sig').read()
n_before = len(s)

# ---------- machine 1: generate() _entry_unpack_info ----------
a = """                    _pre_stmts: List[Dict[str, Any]] = []
                    _stmt_instrs: List[Instruction] = []
                    _import_pending_store = False
                    _entry_unpack_info = None"""
assert a in s, 'm1 init'
s = s.replace(a, a + """
                    # [v153-RESIDUNPACK] 链式解包残栈值队列 + 合并发射持存
                    # （首解包值=栈顶、残栈元素是后续解包值源；独立连续解包
                    # 各有自己的值缓冲不落本路径）。
                    _v153_dual_pending: List[Dict[str, Any]] = []
                    _v153_chain_holds: List[tuple] = []""", 1)

a = """                        if _instr.opname in ('UNPACK_SEQUENCE', 'UNPACK_EX'):
                            _val_instrs = [i for i in _stmt_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                            _val = self.expr_reconstructor.reconstruct(_val_instrs) if _val_instrs else None
                            if _instr.opname == 'UNPACK_SEQUENCE':
                                _entry_unpack_info = {'value': _val, 'targets': [], 'count': _instr.arg}
                            else:
                                _arg = _instr.argval
                                _before, _after = _arg & 0xFF, (_arg >> 8) & 0xFF
                                _entry_unpack_info = {'value': _val, 'targets': [], 'count': _before + 1 + _after, 'is_starred': True, 'starred_idx': _before}
                            _stmt_instrs = []
                            continue"""
assert a in s, 'm1 unpack'
r = """                        if _instr.opname in ('UNPACK_SEQUENCE', 'UNPACK_EX'):
                            _val_instrs = [i for i in _stmt_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                            # [v153-RESIDUNPACK] 值源：有值缓冲走既有 reconstruct
                            # （并捕获残栈为 pending 队列，TOS 在前）；空缓冲且
                            # 紧邻前解包留下残栈时从队列取值。
                            if _val_instrs:
                                _val = self.expr_reconstructor.reconstruct(_val_instrs)
                                _v153_nn = [sx for sx in self.expr_reconstructor.stack
                                            if not (isinstance(sx, dict) and sx.get('type') == 'PUSH_NULL')]
                                _v153_dual_pending = list(reversed(_v153_nn[:-1])) if len(_v153_nn) >= 2 else []
                                _v153_from_residual = False
                            elif _v153_dual_pending:
                                _val = _v153_dual_pending.pop(0)
                                _v153_from_residual = True
                            else:
                                _val = None
                                _v153_from_residual = False
                            if _instr.opname == 'UNPACK_SEQUENCE':
                                _entry_unpack_info = {'value': _val, 'targets': [], 'count': _instr.arg,
                                                      '_v153_from_residual': _v153_from_residual}
                            else:
                                _arg = _instr.argval
                                _before, _after = _arg & 0xFF, (_arg >> 8) & 0xFF
                                _entry_unpack_info = {'value': _val, 'targets': [], 'count': _before + 1 + _after, 'is_starred': True, 'starred_idx': _before,
                                                      '_v153_from_residual': _v153_from_residual}
                            _stmt_instrs = []
                            continue"""
s = s.replace(a, r, 1)

a = """                                if len(_entry_unpack_info['targets']) == _entry_unpack_info['count']:
                                    _target = {'type': 'Tuple', 'elts': _entry_unpack_info['targets'], 'ctx': 'Store'}
                                    if _entry_unpack_info['value']:
                                        _pre_stmts.append({'type': 'Assign', 'targets': [_target], 'value': _entry_unpack_info['value']})
                                    _entry_unpack_info = None"""
assert a in s, 'm1 completion'
r = """                                if len(_entry_unpack_info['targets']) == _entry_unpack_info['count']:
                                    _target = {'type': 'Tuple', 'elts': _entry_unpack_info['targets'], 'ctx': 'Store'}
                                    if _entry_unpack_info['value']:
                                        # [v153-RESIDUNPACK] 完成处后随 UNPACK_* 且
                                        # 本解包值来自残栈时与持存首解包合并发射
                                        # （重编译同一 SWAP+多 UNPACK 形字节等价）；
                                        # 独立连续解包逐位落回既有逐解包发射。
                                        _v153_ni = -1
                                        try:
                                            _v153_ni = entry_block.instructions.index(_instr) + 1
                                        except (ValueError, AttributeError):
                                            _v153_ni = -1
                                        _v153_next = (entry_block.instructions[_v153_ni]
                                                      if 0 <= _v153_ni < len(entry_block.instructions) else None)
                                        if (not _entry_unpack_info.get('_v153_from_residual')
                                                and _v153_next is not None
                                                and _v153_next.opname in ('UNPACK_SEQUENCE', 'UNPACK_EX')):
                                            _v153_chain_holds.append((_target, _entry_unpack_info['value']))
                                            _entry_unpack_info = None
                                            _stmt_instrs = []
                                            continue
                                        if _entry_unpack_info.get('_v153_from_residual') and _v153_chain_holds:
                                            _h_target, _h_value = _v153_chain_holds.pop()
                                            _pre_stmts.append({
                                                'type': 'Assign',
                                                'targets': [{'type': 'Tuple',
                                                             'elts': [_h_target, _target],
                                                             'ctx': 'Store'}],
                                                'value': {'type': 'Tuple',
                                                          'elts': [_h_value, _entry_unpack_info['value']],
                                                          'ctx': 'Load'},
                                            })
                                            _entry_unpack_info = None
                                            _stmt_instrs = []
                                            continue
                                        _pre_stmts.append({'type': 'Assign', 'targets': [_target], 'value': _entry_unpack_info['value']})
                                    _entry_unpack_info = None"""
s = s.replace(a, r, 1)
print('machine 1 patched')

# ---------- machine 2: _loop_extract_self_loop_stmts _sl_unpack_info ----------
a = """        _sl_imp_pairs = []
        _sl_unpack_info = None"""
assert s.count(a) == 1, 'm2 init count %d' % s.count(a)
s = s.replace(a, a + """
        # [v153-RESIDUNPACK] 链式解包残栈值队列 + 合并发射持存（同 _entry 机）。
        _v153_dual_pending: List[Dict[str, Any]] = []
        _v153_chain_holds: List[tuple] = []""", 1)

a = """            if _sli_instr.opname == 'UNPACK_SEQUENCE':
                _vi = [i for i in _self_loop_instrs
                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                _val = self.expr_reconstructor.reconstruct(_vi) if _vi else None
                _sl_unpack_info = {'value': _val, 'targets': [], 'count': _sli_instr.arg,
                                   'is_starred': False, 'starred_idx': -1}
                _self_loop_instrs = []
                continue
            if _sli_instr.opname == 'UNPACK_EX':
                _vi = [i for i in _self_loop_instrs
                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                _val = self.expr_reconstructor.reconstruct(_vi) if _vi else None
                _arg = _sli_instr.argval
                _before, _after = _arg & 0xFF, (_arg >> 8) & 0xFF
                _sl_unpack_info = {'value': _val, 'targets': [],
                                   'count': _before + 1 + _after,
                                   'is_starred': True, 'starred_idx': _before}
                _self_loop_instrs = []
                continue"""
assert a in s, 'm2 unpack'
r = """            if _sli_instr.opname == 'UNPACK_SEQUENCE':
                _vi = [i for i in _self_loop_instrs
                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                # [v153-RESIDUNPACK] 值源（同 _entry 机：残栈 pending 队列）。
                if _vi:
                    _val = self.expr_reconstructor.reconstruct(_vi)
                    _v153_nn = [sx for sx in self.expr_reconstructor.stack
                                if not (isinstance(sx, dict) and sx.get('type') == 'PUSH_NULL')]
                    _v153_dual_pending = list(reversed(_v153_nn[:-1])) if len(_v153_nn) >= 2 else []
                    _v153_from_residual = False
                elif _v153_dual_pending:
                    _val = _v153_dual_pending.pop(0)
                    _v153_from_residual = True
                else:
                    _val = None
                    _v153_from_residual = False
                _sl_unpack_info = {'value': _val, 'targets': [], 'count': _sli_instr.arg,
                                   'is_starred': False, 'starred_idx': -1,
                                   '_v153_from_residual': _v153_from_residual}
                _self_loop_instrs = []
                continue
            if _sli_instr.opname == 'UNPACK_EX':
                _vi = [i for i in _self_loop_instrs
                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                if _vi:
                    _val = self.expr_reconstructor.reconstruct(_vi)
                    _v153_nn = [sx for sx in self.expr_reconstructor.stack
                                if not (isinstance(sx, dict) and sx.get('type') == 'PUSH_NULL')]
                    _v153_dual_pending = list(reversed(_v153_nn[:-1])) if len(_v153_nn) >= 2 else []
                    _v153_from_residual = False
                elif _v153_dual_pending:
                    _val = _v153_dual_pending.pop(0)
                    _v153_from_residual = True
                else:
                    _val = None
                    _v153_from_residual = False
                _arg = _sli_instr.argval
                _before, _after = _arg & 0xFF, (_arg >> 8) & 0xFF
                _sl_unpack_info = {'value': _val, 'targets': [],
                                   'count': _before + 1 + _after,
                                   'is_starred': True, 'starred_idx': _before,
                                   '_v153_from_residual': _v153_from_residual}
                _self_loop_instrs = []
                continue"""
s = s.replace(a, r, 1)

a = """                    if len(_sl_unpack_info['targets']) == _sl_unpack_info['count']:
                        _tgt = {'type': 'Tuple', 'elts': _sl_unpack_info['targets'], 'ctx': 'Store'}
                        if _sl_unpack_info['value'] is not None:
                            _self_loop_stmts.append({'type': 'Assign', 'targets': [_tgt],
                                                     'value': _sl_unpack_info['value']})
                        _sl_unpack_info = None"""
assert a in s, 'm2 completion'
r = """                    if len(_sl_unpack_info['targets']) == _sl_unpack_info['count']:
                        _tgt = {'type': 'Tuple', 'elts': _sl_unpack_info['targets'], 'ctx': 'Store'}
                        if _sl_unpack_info['value'] is not None:
                            # [v153-RESIDUNPACK] 完成处后随 UNPACK_* 且本解包值
                            # 来自残栈时与持存首解包合并发射（同 _entry 机）。
                            _v153_ni = _sli_idx + 1
                            _v153_next = (hdr.instructions[_v153_ni]
                                          if 0 <= _v153_ni < len(hdr.instructions) else None)
                            if (not _sl_unpack_info.get('_v153_from_residual')
                                    and _v153_next is not None
                                    and _v153_next.opname in ('UNPACK_SEQUENCE', 'UNPACK_EX')):
                                _v153_chain_holds.append((_tgt, _sl_unpack_info['value']))
                                _sl_unpack_info = None
                                _self_loop_instrs = []
                                continue
                            if _sl_unpack_info.get('_v153_from_residual') and _v153_chain_holds:
                                _h_target, _h_value = _v153_chain_holds.pop()
                                _self_loop_stmts.append({
                                    'type': 'Assign',
                                    'targets': [{'type': 'Tuple',
                                                 'elts': [_h_target, _tgt],
                                                 'ctx': 'Store'}],
                                    'value': {'type': 'Tuple',
                                              'elts': [_h_value, _sl_unpack_info['value']],
                                              'ctx': 'Load'},
                                })
                                _sl_unpack_info = None
                                _self_loop_instrs = []
                                continue
                            _self_loop_stmts.append({'type': 'Assign', 'targets': [_tgt],
                                                     'value': _sl_unpack_info['value']})
                        _sl_unpack_info = None"""
s = s.replace(a, r, 1)
print('machine 2 patched')

# ---------- machine 4: _loop_process_header_instructions _unpack_info ----------
a = """            if _instr.opname == 'UNPACK_SEQUENCE':
                _val_instrs = [i for i in _hdr_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                _val = self.expr_reconstructor.reconstruct(_val_instrs) if _val_instrs else None
                _unpack_info = {'value': _val, 'targets': [], 'count': _instr.arg}
                _hdr_instrs = []
                continue
            if _instr.opname == 'UNPACK_EX':
                _val_instrs = [i for i in _hdr_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                _val = self.expr_reconstructor.reconstruct(_val_instrs) if _val_instrs else None
                _arg = _instr.argval
                _before = _arg & 0xFF
                _after = (_arg >> 8) & 0xFF
                _unpack_info = {'value': _val, 'targets': [], 'count': _before + 1 + _after, 'is_starred': True, 'starred_idx': _before}
                _hdr_instrs = []
                continue"""
assert a in s, 'm4 unpack'
r = """            if _instr.opname == 'UNPACK_SEQUENCE':
                _val_instrs = [i for i in _hdr_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                # [v153-RESIDUNPACK] 值源（同 _entry 机：残栈 pending 队列）。
                if _val_instrs:
                    _val = self.expr_reconstructor.reconstruct(_val_instrs)
                    _v153_nn = [sx for sx in self.expr_reconstructor.stack
                                if not (isinstance(sx, dict) and sx.get('type') == 'PUSH_NULL')]
                    _v153_dual_pending = list(reversed(_v153_nn[:-1])) if len(_v153_nn) >= 2 else []
                    _v153_from_residual = False
                elif _v153_dual_pending:
                    _val = _v153_dual_pending.pop(0)
                    _v153_from_residual = True
                else:
                    _val = None
                    _v153_from_residual = False
                _unpack_info = {'value': _val, 'targets': [], 'count': _instr.arg,
                                '_v153_from_residual': _v153_from_residual}
                _hdr_instrs = []
                continue
            if _instr.opname == 'UNPACK_EX':
                _val_instrs = [i for i in _hdr_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                if _val_instrs:
                    _val = self.expr_reconstructor.reconstruct(_val_instrs)
                    _v153_nn = [sx for sx in self.expr_reconstructor.stack
                                if not (isinstance(sx, dict) and sx.get('type') == 'PUSH_NULL')]
                    _v153_dual_pending = list(reversed(_v153_nn[:-1])) if len(_v153_nn) >= 2 else []
                    _v153_from_residual = False
                elif _v153_dual_pending:
                    _val = _v153_dual_pending.pop(0)
                    _v153_from_residual = True
                else:
                    _val = None
                    _v153_from_residual = False
                _arg = _instr.argval
                _before = _arg & 0xFF
                _after = (_arg >> 8) & 0xFF
                _unpack_info = {'value': _val, 'targets': [], 'count': _before + 1 + _after, 'is_starred': True, 'starred_idx': _before,
                                '_v153_from_residual': _v153_from_residual}
                _hdr_instrs = []
                continue"""
s = s.replace(a, r, 1)

a = """                    if len(_unpack_info['targets']) == _unpack_info['count']:
                        _target = {'type': 'Tuple', 'elts': _unpack_info['targets'], 'ctx': 'Store'}
                        if _unpack_info['value']:
                            _hdr_stmts.append({'type': 'Assign', 'targets': [_target], 'value': _unpack_info['value']})
                        _unpack_info = None"""
assert a in s, 'm4 completion'
r = """                    if len(_unpack_info['targets']) == _unpack_info['count']:
                        _target = {'type': 'Tuple', 'elts': _unpack_info['targets'], 'ctx': 'Store'}
                        if _unpack_info['value']:
                            # [v153-RESIDUNPACK] 完成处后随 UNPACK_* 且本解包值
                            # 来自残栈时与持存首解包合并发射（同 _entry 机）。
                            _v153_ni = _instr_idx + 1
                            _v153_next = (block.instructions[_v153_ni]
                                          if 0 <= _v153_ni < len(block.instructions) else None)
                            if (not _unpack_info.get('_v153_from_residual')
                                    and _v153_next is not None
                                    and _v153_next.opname in ('UNPACK_SEQUENCE', 'UNPACK_EX')):
                                _v153_chain_holds.append((_target, _unpack_info['value']))
                                _unpack_info = None
                                _hdr_instrs = []
                                _seen_store = True
                                continue
                            if _unpack_info.get('_v153_from_residual') and _v153_chain_holds:
                                _h_target, _h_value = _v153_chain_holds.pop()
                                _hdr_stmts.append({
                                    'type': 'Assign',
                                    'targets': [{'type': 'Tuple',
                                                 'elts': [_h_target, _target],
                                                 'ctx': 'Store'}],
                                    'value': {'type': 'Tuple',
                                              'elts': [_h_value, _unpack_info['value']],
                                              'ctx': 'Load'},
                                })
                                _unpack_info = None
                                _hdr_instrs = []
                                _seen_store = True
                                continue
                            _hdr_stmts.append({'type': 'Assign', 'targets': [_target], 'value': _unpack_info['value']})
                        _unpack_info = None"""
s = s.replace(a, r, 1)

# machine 4 init: locate `_unpack_info = None` (unique context)
a = """        _seen_store = False
        _unpack_info = None
        _break_cause = None"""
assert s.count(a) == 1, 'm4 init count %d' % s.count(a)
s = s.replace(a, a + """
        # [v153-RESIDUNPACK] 链式解包残栈值队列 + 合并发射持存（同 _entry 机）。
        _v153_dual_pending: List[Dict[str, Any]] = []
        _v153_chain_holds: List[tuple] = []""", 1)
print('machine 4 patched')

# ---------- machine 5: _loop_extract_pre_stmts_from_instrs _nbi_unpack_info ----------
a = """        _pre_stmts: List[Dict[str, Any]] = []
        _buf: List[Instruction] = []
        _nbi_unpack_info = None"""
assert s.count(a) == 1, 'm5 init count %d' % s.count(a)
s = s.replace(a, a + """
        # [v153-RESIDUNPACK] 链式解包残栈值队列 + 合并发射持存（同 _entry 机）。
        _v153_dual_pending: List[Dict[str, Any]] = []
        _v153_chain_holds: List[tuple] = []""", 1)

a = """            if _nbi.opname == 'UNPACK_SEQUENCE':
                _val_instrs = [i for i in _buf
                               if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                _val = self.expr_reconstructor.reconstruct(_val_instrs) if _val_instrs else None
                _nbi_unpack_info = {'value': _val, 'targets': [], 'count': _nbi.arg}
                _buf = []
                continue
            if _nbi.opname == 'UNPACK_EX':
                _val_instrs = [i for i in _buf
                               if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                _val = self.expr_reconstructor.reconstruct(_val_instrs) if _val_instrs else None
                _nbi_arg = _nbi.argval
                _before = _nbi_arg & 0xFF
                _after = (_nbi_arg >> 8) & 0xFF
                _nbi_unpack_info = {'value': _val, 'targets': [], 'count': _before + 1 + _after, 'is_starred': True, 'starred_idx': _before}
                _buf = []
                continue"""
assert a in s, 'm5 unpack'
r = """            if _nbi.opname == 'UNPACK_SEQUENCE':
                _val_instrs = [i for i in _buf
                               if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                # [v153-RESIDUNPACK] 值源（同 _entry 机：残栈 pending 队列）。
                if _val_instrs:
                    _val = self.expr_reconstructor.reconstruct(_val_instrs)
                    _v153_nn = [sx for sx in self.expr_reconstructor.stack
                                if not (isinstance(sx, dict) and sx.get('type') == 'PUSH_NULL')]
                    _v153_dual_pending = list(reversed(_v153_nn[:-1])) if len(_v153_nn) >= 2 else []
                    _v153_from_residual = False
                elif _v153_dual_pending:
                    _val = _v153_dual_pending.pop(0)
                    _v153_from_residual = True
                else:
                    _val = None
                    _v153_from_residual = False
                _nbi_unpack_info = {'value': _val, 'targets': [], 'count': _nbi.arg,
                                    '_v153_from_residual': _v153_from_residual}
                _buf = []
                continue
            if _nbi.opname == 'UNPACK_EX':
                _val_instrs = [i for i in _buf
                               if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                if _val_instrs:
                    _val = self.expr_reconstructor.reconstruct(_val_instrs)
                    _v153_nn = [sx for sx in self.expr_reconstructor.stack
                                if not (isinstance(sx, dict) and sx.get('type') == 'PUSH_NULL')]
                    _v153_dual_pending = list(reversed(_v153_nn[:-1])) if len(_v153_nn) >= 2 else []
                    _v153_from_residual = False
                elif _v153_dual_pending:
                    _val = _v153_dual_pending.pop(0)
                    _v153_from_residual = True
                else:
                    _val = None
                    _v153_from_residual = False
                _nbi_arg = _nbi.argval
                _before = _nbi_arg & 0xFF
                _after = (_nbi_arg >> 8) & 0xFF
                _nbi_unpack_info = {'value': _val, 'targets': [], 'count': _before + 1 + _after, 'is_starred': True, 'starred_idx': _before,
                                    '_v153_from_residual': _v153_from_residual}
                _buf = []
                continue"""
s = s.replace(a, r, 1)

a = """                    if len(_nbi_unpack_info['targets']) == _nbi_unpack_info['count']:
                        _target = {
                            'type': 'Tuple',
                            'elts': _nbi_unpack_info['targets'],
                            'ctx': 'Store',
                        }
                        if _nbi_unpack_info['value']:
                            _pre_stmts.append({'type': 'Assign', 'targets': [_target], 'value': _nbi_unpack_info['value']})
                        _nbi_unpack_info = None"""
assert a in s, 'm5 completion'
r = """                    if len(_nbi_unpack_info['targets']) == _nbi_unpack_info['count']:
                        _target = {
                            'type': 'Tuple',
                            'elts': _nbi_unpack_info['targets'],
                            'ctx': 'Store',
                        }
                        if _nbi_unpack_info['value']:
                            # [v153-RESIDUNPACK] 完成处后随 UNPACK_* 且本解包值
                            # 来自残栈时与持存首解包合并发射（同 _entry 机）。
                            _v153_ni = -1
                            try:
                                _v153_ni = instrs.index(_nbi) + 1
                            except (ValueError, AttributeError):
                                _v153_ni = -1
                            _v153_next = (instrs[_v153_ni]
                                          if 0 <= _v153_ni < len(instrs) else None)
                            if (not _nbi_unpack_info.get('_v153_from_residual')
                                    and _v153_next is not None
                                    and _v153_next.opname in ('UNPACK_SEQUENCE', 'UNPACK_EX')):
                                _v153_chain_holds.append((_target, _nbi_unpack_info['value']))
                                _nbi_unpack_info = None
                                _buf = []
                                continue
                            if _nbi_unpack_info.get('_v153_from_residual') and _v153_chain_holds:
                                _h_target, _h_value = _v153_chain_holds.pop()
                                _pre_stmts.append({
                                    'type': 'Assign',
                                    'targets': [{'type': 'Tuple',
                                                 'elts': [_h_target, _target],
                                                 'ctx': 'Store'}],
                                    'value': {'type': 'Tuple',
                                              'elts': [_h_value, _nbi_unpack_info['value']],
                                              'ctx': 'Load'},
                                })
                                _nbi_unpack_info = None
                                _buf = []
                                continue
                            _pre_stmts.append({'type': 'Assign', 'targets': [_target], 'value': _nbi_unpack_info['value']})
                        _nbi_unpack_info = None"""
s = s.replace(a, r, 1)
print('machine 5 patched')

io.open(p, 'w', encoding='utf-8-sig').write(s)
print('fix153 inserted (+%d chars)' % (len(s) - n_before))

import py_compile
py_compile.compile(p, doraise=True)
print('syntax OK')
