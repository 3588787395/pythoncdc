"""R35 candidate builder (R21-27): bound the f-string prefix window at a statement boundary.

Measured cause (rounds/round34/NOTE_R21-27_ast_side_fstring_stack_pollution.md section 6): in
`_generate_ternary` the prefix window `cond_block_instrs[_r65_callee_skip:cond_val_start]` can contain whole
preceding statements. The R66-d2 segmenter is handed that 54-instruction window (measured @1968..@2312,
contains STORE_*) and correctly refuses it, after which the caller falls back to `fstring_parts = _stack`,
which fabricates one JoinedStr part per `LOAD_*` and renders the glued literal
`list_info00orderstrresultentrust_no...` in `trade_live_broker.etf_purchase_redemption`.

Fix: advance the window start past the LAST statement boundary inside it. One variable
(`_r65_callee_skip`) bounds both the per-`LOAD_*` scan (:45048) and the segment loop (:45097), so this is a
single statement-boundary rule rather than a per-unit patch.

usage: python -X utf8 build_cand_r35_R21-27.py <generator-file>
"""
import hashlib
import py_compile
import sys

NEW = [
    "                # [R21-27] 前缀窗口止于最后一条语句边界。cond_block 里 f-string 之前的窗口可能",
    "                # 残留整条前序语句（实测被拒段 @[1968..2312] n=54 含 STORE_*），R66-d2 分段归约",
    "                # 正确地拒绝它，调用方随即回退 fstring_parts = _stack，把每条 LOAD_* 伪造成一个",
    "                # JoinedStr 片段，渲染出 'list_info00orderstrresultentrust_no...' 的粘连字面量。",
    "                # 边界判据只读本块指令流：STORE_*/POP_TOP/DELETE_*/JUMP_*/RETURN_VALUE/",
    "                # RAISE_VARARGS 之后不可能再接本 f-string 的字面片段。",
    "                if cond_val_start is not None and cond_val_start > 0:",
    "                    for _r27_i in range(cond_val_start - 1, _r65_callee_skip - 1, -1):",
    "                        _r27_op = cond_block_instrs[_r27_i].opname",
    "                        if (_r27_op.startswith('STORE_')",
    "                                or _r27_op in ('POP_TOP', 'RETURN_VALUE',",
    "                                                'RAISE_VARARGS')",
    "                                or _r27_op.startswith('DELETE_')",
    "                                or _r27_op.startswith('JUMP_')):",
    "                            _r65_callee_skip = _r27_i + 1",
    "                            break",
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
    anchor = b"                fstring_parts = []"
    hit = [n for n, l in enumerate(lines) if l == anchor]
    assert len(hit) == 1, 'anchor hit %dx at %s' % (len(hit), hit)
    n = hit[0]
    ctx = b'\r\n'.join(lines[max(0, n - 40):n])
    assert b'_r65_callee_skip' in ctx, 'anchor not inside the R65-callee block'
    out = lines[:n] + [x.encode('utf-8') for x in NEW] + lines[n:]
    patched = b'\r\n'.join(out)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('inserted %d lines before :%d (fstring_parts = []) size=%d sha16=%s (was %s) py_compile=OK'
          % (len(NEW), n + 1, len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
