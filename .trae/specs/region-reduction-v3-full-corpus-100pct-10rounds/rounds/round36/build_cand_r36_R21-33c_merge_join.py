"""R36 candidate builder (R21-33 hunk C): when the conditional jump's landing block is also
entered from inside the then arm, it is the if's MERGE, not an exclusive else arm - emit
`if cond: <then>` and leave the merge to sequential reduction.

Trace-proved site (D:/Temp/r36/who_negates_r36.py, single-function generation of
trade_live_broker._trade_status_handle on top of the hunk-B analyzer): line 13415
`_hdr_stmts.append({'type': 'If', 'test': _negated_expr2, ...})` inside
`_loop_handle_no_exit_successors`, branch `if _else_is_continue and not _then_is_continue:`
with `_then_is_trivial == False`. For the victim `_break_cause` = @148 POP_JUMP_FORWARD_IF_FALSE,
`_then_succ` = @150 (the real body), `_else_succ` = @830 = `time.sleep(0.5)` +
`JUMP_BACKWARD -> 46`, whose predecessors are {@46 (the cond block itself), @720, @722}.
Because @720/@722 live inside the then arm, @830 is reached by BOTH arms: it is the join of the
`if`, and the true source shape is

    while True:
        <header statements>
        if self.trade_status != trade_status:
            <body>
        time.sleep(0.5)

which the compiled-shape dump (D:/Temp/r36/shape_tails2.py) matches to the original's signature:
NOP continue target, ONE top test, unconditional JUMP_BACKWARD, no trailing return tail. The
current branch instead emits `if not cond: time.sleep(0.5); continue`, which puts the sleep in
front of the body - measured on hunk B alone as delta=+1 hunks=2 (`del=1 ins=8` @148 plus a
`del=6` @830) - and no flip.

This is the dual of the branch already at :13369 (`_then_is_pure_cont`: emit `if cond: continue`
and leave the other block to sequential reduction, its JUMP_BACKWARD suppressed as the implicit
back edge). Own-data only: the cond block, the two successors and the landing block's predecessors.

usage: python -X utf8 build_cand_r36_R21-33c_merge_join.py <region_ast_generator.py>
"""
import hashlib
import py_compile
import sys

OLD = [
    "                if _else_is_continue and not _then_is_continue:",
    "                    _then_is_trivial = True",
]

NEW = [
    "                if _else_is_continue and not _then_is_continue:",
    "                    # [R21-33c] 落点块另有来自 then 侧内部的前驱时，它是本 if 的汇合点而不是独占",
    "                    # 分支：发射 `if cond: <then>` 并把汇合块留给循环体顺序归约（其 JUMP_BACKWARD",
    "                    # 作为隐式回边被分发抑制）。与 :13369「then 为纯 continue」分支对偶。",
    "                    _r33_join = (_then_succ is not None and any(",
    "                        p is not block and p is not _else_succ",
    "                        and p.start_offset >= _then_succ.start_offset",
    "                        for p in _else_succ.predecessors))",
    "                    if _r33_join:",
    "                        _r33_then_stmts = self._generate_block_statements(_then_succ)",
    "                        if not _r33_then_stmts:",
    "                            _r33_then_stmts = [{'type': 'Pass'}]",
    "                        self.generated_blocks.add(_then_succ)",
    "                        self.generated_offsets.add(_then_succ.start_offset)",
    "                        _hdr_stmts.append({'type': 'If', 'test': _expr,",
    "                                           'body': _r33_then_stmts})",
    "                        return",
    "                    _then_is_trivial = True",
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
    assert len(hits) == 1, 'anchor hits %d (_else_is_continue branch must be unique)' % len(hits)
    n = hits[0]
    ctx = b'\r\n'.join(lines[max(0, n - 80):n])
    assert b'def _loop_handle_no_exit_successors' in ctx, 'anchor not in _loop_handle_no_exit_successors'
    out = lines[:n] + [x.encode('utf-8') for x in NEW] + lines[n + len(ob):]
    patched = b'\r\n'.join(out)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('replaced %d lines with %d at :%d size=%d sha16=%s (was %s) py_compile=OK'
          % (len(OLD), len(NEW), n + 1, len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
