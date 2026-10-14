"""R35 candidate builder (R21-27c): skip ALL leading pending-callee groups, not just the first.

Applied after build_cand_r35_R21-27.py (prefix-window bound) and build_cand_r35b_R21-27_chain.py
(chain wrap). Measured state before this hunk: etf_purchase_redemption -12/5/0 -> -2/4/0 with the
statement restored to `strategy_log.info(_(f"..."))`, but the outer callee name is still rendered into
the literal (`f"strategy_log_生成订单，订单号：..."`), because [R65-d3 C1a] removes only ONE callee group
from the prefix window while `x.m(_(f'..'))` pushes two (strategy_log.info, then the gettext `_`).

Rule added: inside the bounded window, skip leading callee groups of exactly the forms C1a already
recognises ([PUSH_NULL] + LOAD_GLOBAL/LOAD_NAME/LOAD_FAST/LOAD_DEREF + LOAD_ATTR/LOAD_METHOD*) until the
first instruction that cannot start such a group (LOAD_CONST / FORMAT_VALUE / BUILD_* / ...). Those skipped
groups are the outer Call.func chain (NOTE_R21-27b §1), never f-string parts.

usage: python -X utf8 build_cand_r35c_R21-27_callee_skip.py <generator-file>
"""
import hashlib
import py_compile
import sys

OLD = [
    "                        if (_r27_op.startswith('STORE_')",
    "                                or _r27_op in ('POP_TOP', 'RETURN_VALUE',",
    "                                                'RAISE_VARARGS')",
    "                                or _r27_op.startswith('DELETE_')",
    "                                or _r27_op.startswith('JUMP_')):",
    "                            _r65_callee_skip = _r27_i + 1",
    "                            break",
]

NEW = [
    "                        if (_r27_op.startswith('STORE_')",
    "                                or _r27_op in ('POP_TOP', 'RETURN_VALUE',",
    "                                                'RAISE_VARARGS')",
    "                                or _r27_op.startswith('DELETE_')",
    "                                or _r27_op.startswith('JUMP_')):",
    "                            _r65_callee_skip = _r27_i + 1",
    "                            break",
    "                # [R21-27c] 窗口开头连续的「本块内未消费的 callee 压栈」组全部剔除：",
    "                # [R65-d3 C1a] 只跳一组，x.m(_(f'..')) 压了两组（strategy_log.info 与 gettext 的 _），",
    "                # 剩下那组被逐条 LOAD_* 扫描渲染成假字面量（实测 f\"strategy_log_生成订单…\"）。",
    "                # 组形态沿用 C1a 的同一判据：[PUSH_NULL]? LOAD_{GLOBAL,NAME,FAST,DEREF}",
    "                # (LOAD_ATTR|LOAD_METHOD)*；遇到不可能开启该组的指令（LOAD_CONST/FORMAT_VALUE/",
    "                # BUILD_*/比较/算术等）即停止，因此真正的字面片段永不被吞。",
    "                if cond_val_start is not None and cond_val_start > 0:",
    "                    _r27c_i = _r65_callee_skip",
    "                    while _r27c_i < cond_val_start:",
    "                        _r27c_a = cond_block_instrs[_r27c_i]",
    "                        if _r27c_a.opname == 'PUSH_NULL':",
    "                            _r27c_i += 1",
    "                            if _r27c_i >= cond_val_start:",
    "                                break",
    "                            _r27c_a = cond_block_instrs[_r27c_i]",
    "                        if _r27c_a.opname not in ('LOAD_GLOBAL', 'LOAD_NAME',",
    "                                                  'LOAD_FAST', 'LOAD_DEREF'):",
    "                            break",
    "                        _r27c_null = (isinstance(_r27c_a.arg, int)",
    "                                      and bool(_r27c_a.arg & 1))",
    "                        _r27c_j = _r27c_i + 1",
    "                        _r27c_attrs = 0",
    "                        while _r27c_j < cond_val_start and cond_block_instrs[",
    "                                _r27c_j].opname in ('LOAD_ATTR', 'LOAD_METHOD'):",
    "                            _r27c_attrs += 1",
    "                            _r27c_j += 1",
    "                        if not _r27c_null and _r27c_attrs == 0:",
    "                            break",
    "                        _r65_callee_skip = _r27c_j",
    "                        _r27c_i = _r27c_j",
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
    assert len(hits) == 1, 'anchor hits %d' % len(hits)
    n = hits[0]
    out = lines[:n + len(ob)] + [x.encode('utf-8') for x in NEW] + lines[n + len(ob):]
    patched = b'\r\n'.join(out)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('inserted %d lines after :%d size=%d sha16=%s (was %s) py_compile=OK'
          % (len(NEW) - len(OLD), n + len(NEW), len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
