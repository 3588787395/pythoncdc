"""R35 candidate builder (R21-27b): accept a multi-call tail in the f-string pending-call wrap.

Measured cause: `_try_wrap_fstring_pending_call` screens BUILD_STRING's tail with a single
(PRECALL|KW_NAMES)* -> CALL pair and then requires POP_TOP. `trade_live_broker.etf_purchase_redemption`
is the gettext idiom `strategy_log.info(_(f'...'))`, whose merge tail is TWO arg-1 call pairs before
POP_TOP, so `_rest[0]` is the second PRECALL, the screen returns None, and the statement degrades to
`return f'...'`, losing both calls and the following `return order.order_id` (measured -12 / 5 hunks).

Population (D:/Temp/r35_chain_census.py over the verification face): 36 sites with one call pair
(the existing, untouched path) and 3 with two: etf_purchase_redemption, _process_order (both failing)
and get_covered_amount (green, so the panel must watch it).

Requires the banked prefix-window bound (build_cand_r35_R21-27.py) as a co-requisite: apply that first.
usage: python -X utf8 build_cand_r35b_R21-27_chain.py <generator-file>
"""
import hashlib
import py_compile
import sys

HELPER = [
    "    def _ternary_pending_callee_chain(self, cond_block):",
    "        \"\"\"[R21-27b] cond_block 前缀里所有「本块内未被 CALL 消费」的被调对象压栈，按出现顺序返回。",
    "",
    "        识别条件与 _ternary_pending_callee 同一条栈语义判据，只是不再只看第一条：顺序扫描前缀，",
    "        [PUSH_NULL] 或 LOAD_GLOBAL 的 NULL 低位标记开头的 callee 压栈入 pending，遇 CALL 弹出最近",
    "        一个（说明该 callee 在本块内被消费，如 {abs(amount)} 的 abs），扫描结束后仍留在栈上的即",
    "        跨块待定 callee 链（外→内）。不引入函数名/文件名/偏移/阈值判据，不跨区域。",
    "        归约方式：每个待定组归约为 Name 或其上的 Attribute 链，与既有单 callee 分支同形。",
    "        AST 映射：嵌套 Call 的每一层 func；链长为 1 时结果与 _ternary_pending_callee 一致。",
    "        \"\"\"",
    "        if cond_block is None:",
    "            return []",
    "        _cc_instrs = [i for i in cond_block.instructions",
    "                      if i.opname not in ('RESUME', 'NOP', 'CACHE')]",
    "        _cc_end = len(_cc_instrs)",
    "        _cc_last = cond_block.get_last_instruction()",
    "        if _cc_last and _cc_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS",
    "                                            | SHORT_CIRCUIT_JUMP_OPS):",
    "            for _cc_i in range(len(_cc_instrs) - 1, -1, -1):",
    "                if _cc_instrs[_cc_i] is _cc_last:",
    "                    _cc_end = _cc_i",
    "                    break",
    "        _cc_prefix = _cc_instrs[:_cc_end]",
    "        _cc_pending = []",
    "        _cc_i = 0",
    "        while _cc_i < len(_cc_prefix):",
    "            _cc_ins = _cc_prefix[_cc_i]",
    "            _cc_null = (_cc_ins.opname in ('LOAD_GLOBAL', 'LOAD_NAME')",
    "                        and isinstance(_cc_ins.arg, int) and (_cc_ins.arg & 1))",
    "            if _cc_ins.opname == 'PUSH_NULL' or _cc_null:",
    "                _cc_b = _cc_i + 1 if _cc_ins.opname == 'PUSH_NULL' else _cc_i",
    "                _cc_bi = _cc_prefix[_cc_b] if _cc_b < len(_cc_prefix) else None",
    "                if (_cc_bi is not None and _cc_bi.opname in",
    "                        ('LOAD_GLOBAL', 'LOAD_NAME', 'LOAD_FAST', 'LOAD_DEREF')):",
    "                    _cc_node = {'type': 'Name', 'id': _cc_bi.argval, 'ctx': 'Load'}",
    "                    _cc_j = _cc_b + 1",
    "                    while (_cc_j < len(_cc_prefix)",
    "                           and _cc_prefix[_cc_j].opname in ('LOAD_ATTR', 'LOAD_METHOD')",
    "                           and isinstance(_cc_prefix[_cc_j].argval, str)):",
    "                        _cc_node = {'type': 'Attribute', 'value': _cc_node,",
    "                                    'attr': _cc_prefix[_cc_j].argval, 'ctx': 'Load'}",
    "                        _cc_j += 1",
    "                    _cc_pending.append(_cc_node)",
    "                    _cc_i = _cc_b + 1 if _cc_ins.opname == 'PUSH_NULL' else _cc_i + 1",
    "                    continue",
    "            if _cc_ins.opname == 'CALL' and _cc_pending:",
    "                _cc_pending.pop()",
    "            _cc_i += 1",
    "        return _cc_pending",
    "",
]

OLD_SCREEN = [
    "        _tail = eff[_bs + 1:]",
    "        _j = 0",
    "        while _j < len(_tail) and _tail[_j].opname in ('PRECALL', 'KW_NAMES'):",
    "            _j += 1",
    "        if _j == 0 or _j >= len(_tail) or _tail[_j].opname != 'CALL':",
    "            return None",
    "        if (_tail[_j].arg or 0) != 1:",
    "            return None",
    "        _callee = self._ternary_pending_callee(region.condition_block)",
    "        if _callee is None:",
    "            return None",
    "        _rest = _tail[_j + 1:]",
]

NEW_SCREEN = [
    "        _tail = eff[_bs + 1:]",
    "        # [R21-27b] 尾部调用对数：BUILD_STRING 之后连续的 PRECALL?/KW_NAMES* + CALL(arg==1) 对。",
    "        # 既有实现只认一对（x.m(f'...')）；gettext 惯用法 x.m(_(f'...')) 是两对，第二对的",
    "        # PRECALL 使末判据 _rest[0] != POP_TOP 退回，语句被降级为 return f'...' 并丢掉后续语句。",
    "        # 对数==1 时逐字节沿用既有路径（语料实测 36 处），仅 >1 时才走链式扩展。",
    "        _r27_pairs = 0",
    "        _r27_k = 0",
    "        while _r27_k < len(_tail):",
    "            _r27_m = _r27_k",
    "            while (_r27_m < len(_tail)",
    "                   and _tail[_r27_m].opname in ('PRECALL', 'KW_NAMES')):",
    "                _r27_m += 1",
    "            if _r27_m >= len(_tail) or _tail[_r27_m].opname != 'CALL':",
    "                break",
    "            if (_tail[_r27_m].arg or 0) != 1:",
    "                break",
    "            _r27_pairs += 1",
    "            _r27_k = _r27_m + 1",
    "        if _r27_pairs == 0:",
    "            return None",
    "        if _r27_pairs == 1:",
    "            _j = 0",
    "            while _j < len(_tail) and _tail[_j].opname in ('PRECALL', 'KW_NAMES'):",
    "                _j += 1",
    "            if _j == 0 or _j >= len(_tail) or _tail[_j].opname != 'CALL':",
    "                return None",
    "            if (_tail[_j].arg or 0) != 1:",
    "                return None",
    "            _callee = self._ternary_pending_callee(region.condition_block)",
    "            if _callee is None:",
    "                return None",
    "            _r27_funcs = None",
    "            _rest = _tail[_j + 1:]",
    "        else:",
    "            _r27_funcs = self._ternary_pending_callee_chain(region.condition_block)",
    "            if len(_r27_funcs) != _r27_pairs:",
    "                return None",
    "            _callee = _r27_funcs[0]",
    "            _rest = _tail[_r27_k:]",
]

OLD_RET = [
    "        return {",
    "            'type': 'Expr',",
    "            'value': {",
    "                'type': 'Call',",
    "                'func': _callee,",
    "                'args': [joined_str],",
    "                'keywords': [],",
    "            },",
    "        }",
]

NEW_RET = [
    "        if _r27_funcs:",
    "            # 外→内的待定 callee 逐层嵌套：最内层包住 JoinedStr，最外层即 _callee。",
    "            _r27_value = joined_str",
    "            for _r27_f in reversed(_r27_funcs):",
    "                _r27_value = {'type': 'Call', 'func': _r27_f,",
    "                              'args': [_r27_value], 'keywords': []}",
    "        else:",
    "            _r27_value = {'type': 'Call', 'func': _callee,",
    "                          'args': [joined_str], 'keywords': []}",
    "        return {'type': 'Expr', 'value': _r27_value}",
]


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def find_block(lines, block):
    hits = []
    for n in range(len(lines) - len(block) + 1):
        if lines[n:n + len(block)] == [x.encode('utf-8') for x in block]:
            hits.append(n)
    return hits


def main():
    target = sys.argv[1]
    raw = open(target, 'rb').read()
    pre = sha16(raw)
    assert raw.startswith(b'\xef\xbb\xbf'), 'expected BOM'
    assert raw.count(b'\n') == raw.count(b'\r\n'), 'mixed newlines - refuse'
    lines = raw.split(b'\r\n')

    hits = find_block(lines, OLD_SCREEN)
    assert len(hits) == 1, 'screen block hits %d' % len(hits)
    s = hits[0]
    r = find_block(lines, OLD_RET)
    assert len(r) == 1, 'return block hits %d' % len(r)
    hr = find_block(lines, ["    def _try_wrap_fstring_pending_call(self, region, innermost_merge, joined_str):"])
    assert len(hr) == 1, 'helper anchor hits %d' % len(hr)

    out = list(lines)
    # replace bottom-up so earlier indices stay valid
    out[r[0]:r[0] + len(OLD_RET)] = [x.encode('utf-8') for x in NEW_RET]
    out[s:s + len(OLD_SCREEN)] = [x.encode('utf-8') for x in NEW_SCREEN]
    out[hr[0]:hr[0]] = [x.encode('utf-8') for x in HELPER]
    patched = b'\r\n'.join(out)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('patched screen(+%d)/return(+%d)/helper(+%d) size=%d sha16=%s (was %s) py_compile=OK'
          % (len(NEW_SCREEN) - len(OLD_SCREEN), len(NEW_RET) - len(OLD_RET), len(HELPER),
             len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
