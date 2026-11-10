# fix153c.py: [v153-RESIDUNPACK] _generate_stmts_from_instrs unpack machine
import io

p = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
s = io.open(p, encoding='utf-8-sig').read()

a = """            if _instr.opname in ('UNPACK_EX', 'UNPACK_SEQUENCE') and _buf:
                _unpack_value_instrs = list(_buf)
                _unpack_value_expr = self.expr_reconstructor.reconstruct(_unpack_value_instrs)
                _unpack_targets: List[Dict[str, Any]] = []
                _uj = _gi + 1"""
assert s.count(a) == 1, 'gi unpack count %d' % s.count(a)
r = """            if _instr.opname in ('UNPACK_EX', 'UNPACK_SEQUENCE') and (_buf or _v153_dual_pending):
                # [v153-RESIDUNPACK] 值源：有值缓冲走既有 reconstruct（并捕获残栈
                # 为 pending 队列，TOS 在前）；空缓冲且紧邻前解包留下残栈时从队列
                # 取值（兄弟链 `(a, b), (c, d) = x, y` 的 SWAP 形次级值源）。
                if _buf:
                    _unpack_value_instrs = list(_buf)
                    _unpack_value_expr = self.expr_reconstructor.reconstruct(_unpack_value_instrs)
                    _v153_nn = [sx for sx in self.expr_reconstructor.stack
                                if not (isinstance(sx, dict) and sx.get('type') == 'PUSH_NULL')]
                    _v153_dual_pending = list(reversed(_v153_nn[:-1])) if len(_v153_nn) >= 2 else []
                    _v153_from_residual = False
                else:
                    _unpack_value_expr = _v153_dual_pending.pop(0)
                    _v153_from_residual = True
                _unpack_targets: List[Dict[str, Any]] = []
                _uj = _gi + 1"""
s = s.replace(a, r, 1)

a = """                if _unpack_value_expr is not None and _unpack_targets:
                    _unpack_target = {'type': 'Tuple', 'elts': _unpack_targets, 'ctx': 'Store'}
                    _stmts.append({'type': 'Assign', 'targets': [_unpack_target], 'value': _unpack_value_expr})
                    _buf = []
                    _gi = _uj
                    continue"""
assert s.count(a) == 1, 'gi completion count %d' % s.count(a)
r = """                if _unpack_value_expr is not None and _unpack_targets:
                    _unpack_target = {'type': 'Tuple', 'elts': _unpack_targets, 'ctx': 'Store'}
                    # [v153-RESIDUNPACK] 顶层完成处：后随 UNPACK_* 且残栈队列非空
                    # 时持存（不立即发射）；持存帧与来自残栈的链帧合并发射（重编译
                    # 同一 SWAP+多 UNPACK 形字节等价）；独立连续解包（链帧有自己的
                    # 值缓冲）逐位落回既有逐解包发射。
                    _v153_nx = (instrs[_uj] if _uj < _gn else None)
                    _v153_should_hold = (_v153_nx is not None
                                         and _v153_nx.opname in ('UNPACK_SEQUENCE', 'UNPACK_EX')
                                         and bool(_v153_dual_pending))
                    if _v153_from_residual and _v153_chain_holds:
                        _h_target, _h_value = _v153_chain_holds.pop()
                        _stmts.append({
                            'type': 'Assign',
                            'targets': [{'type': 'Tuple',
                                         'elts': [_h_target, _unpack_target],
                                         'ctx': 'Store'}],
                            'value': {'type': 'Tuple',
                                      'elts': [_h_value, _unpack_value_expr],
                                      'ctx': 'Load'},
                        })
                    elif _v153_should_hold:
                        _v153_chain_holds.append((_unpack_target, _unpack_value_expr))
                    else:
                        _stmts.append({'type': 'Assign', 'targets': [_unpack_target], 'value': _unpack_value_expr})
                    _buf = []
                    _gi = _uj
                    continue"""
s = s.replace(a, r, 1)

# init
a = """    def _generate_stmts_from_instrs(self, instrs: List[Instruction], block: BasicBlock"""
assert s.count(a) == 1, 'gi def count %d' % s.count(a)
# insert init after the def's docstring-less body start — find the first statement following the signature; use the _buf init anchor if present
import re
m = re.search(r"def _generate_stmts_from_instrs\(.*?\n(.*?)\n\n", s, re.S)
# simpler: find `        _buf: List[Instruction] = []` near that def
idx = s.find(a)
seg = s[idx:idx + 3000]
a2 = None
for cand in ("        _buf: List[Instruction] = []", "        _buf = []"):
    if cand in seg:
        a2 = cand
        break
assert a2, 'gi buf init not found'
# first occurrence in segment
pos = idx + seg.find(a2)
line_end = s.find('\n', pos)
insertion = """
        # [v153-RESIDUNPACK] 链式解包残栈值队列 + 合并发射持存（同 _entry 机）。"""
s = s[:line_end] + insertion + s[line_end:]
print('machine _gi patched')

io.open(p, 'w', encoding='utf-8-sig').write(s)

import py_compile
py_compile.compile(p, doraise=True)
print('syntax OK')
