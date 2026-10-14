"""R36 candidate builder (R21-33 hunk A): split the degenerate-while init prefix on STORE_ATTR/STORE_SUBSCR.

Measured (gate-35 base, mirror-only diagnostics): `_trade_status_handle` loses the statement
`self.trade_info = get_trade_status(self.trade_id, True)` (orig @46..@90, del=9). CPython fused three
statements into one maximal straight-line block that the analyzer declares as the loop header (@46,
20 instructions, role=LOOP_HEADER), and `_loop_generate_while`'s degenerate-while prefix splitter
(region_ast_generator.py:7671-7686) closes a statement only on STORE_FAST/STORE_NAME/STORE_DEREF.
So the first assignment (terminated by STORE_ATTR @90) never closed, the buffer kept accumulating into the
second statement, and one `_build_statement` call over the merged 14 instructions (@46..@124, captured with
a stack trace) returned a single Assign — the first statement vanished from the AST entirely
(no `Assign(targets=[Attribute(self,'trade_info')], value=Call(get_trade_status, ...))` exists in the tree).

The two sibling prefix walkers already carry exactly this boundary — `_loop_process_header_instructions`
(:12873 STORE_ATTR / :12867 STORE_SUBSCR) and the `_eps_*` walk inside `_loop_generate_while`
(:7490 / :7497) - so this mirrors an existing in-file decision instead of inventing a predicate.

usage: python -X utf8 build_cand_r36_R21-33a_store_split.py <generator-file>
"""
import hashlib
import py_compile
import sys

OLD = [
    "                    if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF'):",
    "                        if skip_store_targets and instr.argval in skip_store_targets:",
    "                            _init_instrs = []",
    "                            continue",
]

NEW = [
    "                    # [R21-33a] STORE_ATTR/STORE_SUBSCR 同样是语句边界：CPython 把「先求值、后压对象」",
    "                    # 的多条语句融进循环 header 块时，只按 STORE_FAST/NAME/DEREF 断句会把前一条赋值",
    "                    # 累积进后一条（_trade_status_handle 实测 @46..@90 的 self.trade_info =",
    "                    # get_trade_status(self.trade_id, True) 与 @100..@124 的 trade_status =",
    "                    # self.trade_info[2] 合成一次 14 指令 _build_statement 调用，只剩一条 Assign 产出）。",
    "                    # 断句方式与本文件两处同族前缀扫描逐条一致：",
    "                    #   _loop_process_header_instructions(:12867 STORE_SUBSCR / :12873 STORE_ATTR)、",
    "                    #   _loop_generate_while 的 _eps_* 扫描(:7490 / :7497)。",
    "                    if instr.opname in ('STORE_ATTR', 'STORE_SUBSCR'):",
    "                        _init_instrs.append(instr)",
    "                        if instr.opname == 'STORE_ATTR':",
    "                            _r33_st = self._build_attr_assign(_init_instrs)",
    "                        else:",
    "                            _r33_st = self._build_subscript_assign(_init_instrs)",
    "                        if _r33_st:",
    "                            init_stmts.append(_r33_st)",
    "                        _init_instrs = []",
    "                        continue",
    "                    if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF'):",
    "                        if skip_store_targets and instr.argval in skip_store_targets:",
    "                            _init_instrs = []",
    "                            continue",
]


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def main():
    target = sys.argv[1]
    raw = open(target, 'rb').read()
    pre = sha16(raw)
    assert raw.startswith(b'\xef\xbb\xbf'), 'expected BOM'
    assert raw.count(b'\n') == raw.count(b'\r\n'), 'mixed newlines - refuse'
    lines = raw.split(b'\r\n')
    ob = [x.encode('utf-8') for x in OLD]
    hits = [n for n in range(len(lines) - len(ob) + 1) if lines[n:n + len(ob)] == ob]
    assert len(hits) == 1, 'anchor hits %d (degenerate-while splitter must be unique)' % len(hits)
    n = hits[0]
    ctx = b'\r\n'.join(lines[max(0, n - 30):n])
    assert b'is_degenerate_while' in ctx, 'anchor not inside the degenerate-while branch'
    out = lines[:n] + [x.encode('utf-8') for x in NEW] + lines[n + len(ob):]
    patched = b'\r\n'.join(out)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('replaced %d lines with %d at :%d size=%d sha16=%s (was %s) py_compile=OK'
          % (len(OLD), len(NEW), n + 1, len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
