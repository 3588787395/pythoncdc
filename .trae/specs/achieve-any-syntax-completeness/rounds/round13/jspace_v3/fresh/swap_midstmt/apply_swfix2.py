# Apply SWAP-path fix using the file's own segment as the exact OLD text.
import sys

P = r'F:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py'
raw = open(P, 'rb').read().decode('utf-8')
assert '\r\n' in raw and raw.replace('\r\n', '').count('\n') == 0
src = raw.replace('\r\n', '\n')
lines = src.split('\n')

# segment: file lines 67280..67297 (1-based) -> idx 67279..67297
OLD_LINES = lines[67279:67297]
# sanity checks
assert '_last_swap_store_idx = _swap_idx + 1 + _consume_idx' in OLD_LINES[1], OLD_LINES[1]
assert OLD_LINES[-1].strip() == '})', OLD_LINES[-1]
assert '_swap_unpack_stmts.append' in OLD_LINES[14], OLD_LINES[14]
OLD = '\n'.join(OLD_LINES) + '\n'

NEW = """                                # \u5904\u7406 SWAP+STORE \u4e4b\u540e\u7684\u5269\u4f59\u6307\u4ee4\uff08\u5982 RETURN_VALUE\uff09
                                _last_swap_store_idx = _swap_idx + 1 + _consume_idx  # in _chain_instrs
                                _swap_remaining = _chain_instrs[_last_swap_store_idx:]
                                if _swap_remaining:
                                    # [sw-B238-V5R88] \u5269\u4f59\u6bb5\u6309\u8bed\u53e5\u8fb9\u754c\u5207\u5206\uff1a\u672b STORE \u4e0e
                                    # RETURN_VALUE \u4e4b\u95f4\u53ef\u80fd\u65e2\u6709\u5b8c\u6574\u7684\u5144\u5f1f\u8bed\u53e5\uff08\u5982
                                    # wrapper = g(...)\u3001wrapper.p = lambda: ...\uff09\u53c8\u6709
                                    # return \u503c\u8868\u8fbe\u5f0f\u3002\u65e7\u5b9e\u73b0\u628a\u6574\u6bb5\u5f53\u5355\u4e00 return
                                    # \u503c\u91cd\u5efa\uff08reconstruct \u53ea\u53d6\u6808\u9876\uff0c\u5144\u5f1f\u8bed\u53e5\u9759\u9ed8\u4e22\u5f03\uff09\uff0c
                                    # \u4e14\u65e0 RETURN \u65f6\u6574\u6bb5\u4e22\u5f03\uff08REAL46-003 functools.lru_cache
                                    # elif \u5206\u652f\u5b9e\u6d4b\u4e22 wrapper = _lru_cache_wrapper(...) \u4e0e
                                    # wrapper.cache_parameters = lambda: ... \u4e24\u6761\u4e2d\u6bb5\u8bed\u53e5\uff1b
                                    # x1/y1 \u6700\u5c0f\u590d\u73b0\u540c\uff09\u3002\u4e0e\u65e2\u6709 [B238-V3R42] noswap \u8def\u5f84
                                    # \u540c\u4e00\u5224\u636e\uff1a\u4ece RETURN \u4e4b\u524d\u56de\u626b\u5230\u6700\u8fd1\u4e00\u6761\u8bed\u53e5\u7ec8\u7ed3
                                    # \u6307\u4ee4\uff08_B54_STMT_TERMINATOR_OPS\uff0c\u5757\u5185 opcode \u5e8f\uff0cI.4
                                    # \u767d\u540d\u5355\uff09\uff0c\u5176\u524d\u4ea4\u8bed\u53e5\u91cd\u5efa\u5668\u6210\u5144\u5f1f\u8bed\u53e5\uff0c\u5176\u540e\u624d\u662f
                                    # return \u503c\u540e\u7f00\uff1b\u65e0 RETURN \u65f6\u5269\u4f59\u6bb5\u6574\u4f53\u6309\u5144\u5f1f\u8bed\u53e5\u91cd\u5efa\u3002
                                    # \u4e0d\u542b\u7ec8\u7ed3\u6307\u4ee4\u7684\u6bb5\u4e0d\u53ef\u80fd\u542b\u8bed\u53e5\u8fb9\u754c\uff0c\u884c\u4e3a\u4e0e\u65e7\u5b9e\u73b0\u9010\u4f4d
                                    # \u76f8\u540c\uff08C3\uff09\uff1b\u524d\u5bfc\u6bb5\u542b\u8df3\u8f6c\u6307\u4ee4\uff08\u7ed3\u6784\u4e8b\u5b9e\uff09\u65f6\u4e0d\u91cd\u5efa\u3001
                                    # \u7ef4\u6301\u65e7\u4fdd\u5b88\u884c\u4e3a\uff08\u4e0e B238 \u8def\u5f84\u540c\u5b88\u536b\uff09\u3002
                                    _sw_ret_idx = next(
                                        (_k for _k, _i in enumerate(_swap_remaining)
                                         if _i.opname in ('RETURN_VALUE', 'RETURN_CONST')),
                                        len(_swap_remaining))
                                    _sw_body = _swap_remaining[:_sw_ret_idx]
                                    _rv_start_sw = len(_sw_body)
                                    while (_rv_start_sw > 0
                                           and _sw_body[_rv_start_sw - 1].opname
                                           not in self._B54_STMT_TERMINATOR_OPS):
                                        _rv_start_sw -= 1
                                    _pre_body_sw = [
                                        _i for _i in _sw_body[:_rv_start_sw]
                                        if _i.opname not in ('RESUME', 'NOP', 'CACHE',
                                                             'PUSH_NULL', 'POP_TOP', 'COPY',
                                                             'SWAP', 'POP_EXCEPT',
                                                             'PUSH_EXC_INFO')]
                                    _has_jump_sw = any(
                                        _i.opname.startswith('JUMP')
                                        or _i.opname.startswith('POP_JUMP')
                                        or _i.opname == 'FOR_ITER'
                                        for _i in _pre_body_sw)
                                    if _pre_body_sw and not _has_jump_sw:
                                        _pre_stmts_sw = self._build_statements_from_instructions(
                                            _pre_body_sw)
                                        if _pre_stmts_sw:
                                            _swap_unpack_stmts.extend(_pre_stmts_sw)
                                    if _sw_ret_idx < len(_swap_remaining):
                                        _rv_instrs = []
                                        for _instr in _sw_body[_rv_start_sw:]:
                                            if _instr.opname not in ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL',
                                                                    'COPY', 'SWAP', 'POP_EXCEPT', 'PUSH_EXC_INFO'):
                                                _rv_instrs.append(_instr)
                                        _return_value = self.expr_reconstructor.reconstruct(_rv_instrs) if _rv_instrs else None
                                        _swap_unpack_stmts.append({
                                            'type': 'Return',
                                            'value': _return_value if _return_value else {'type': 'Constant', 'value': None}
                                        })
"""

cnt = src.count(OLD)
print('occurrences:', cnt)
assert cnt == 1
src = src.replace(OLD, NEW)
open(P, 'wb').write(src.replace('\n', '\r\n').encode('utf-8'))
print('applied, new line count delta:', len(src.split('\n')) - len(lines))
