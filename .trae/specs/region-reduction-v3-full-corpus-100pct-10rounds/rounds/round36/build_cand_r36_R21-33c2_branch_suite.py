"""R36 candidate builder (R21-33 hunk C2): render the header-test's then side with the SUITE
renderer (`_if_generate_branch_stmts`), then emit the merge block after the `if`.

Why C failed and what this changes (all measured, `rounds/round36/FIX_R21-33_r36.md` §3): hunk C
used `self._generate_block_statements(_then_succ)`, which renders ONE block's own instructions and
never dispatches the nested regions living in it - for `_trade_status_handle` that collapsed the
body to `if cond: self.trade_status = trade_status` and leaked the rest flat at loop level
(`delta=-85 hunks=2`, a regression). The loop-body renderer uses the suite path instead
(`region_ast_generator.py:14640 branch_stmts = self._if_generate_branch_stmts(body_blocks_no_header)`
→ `_process_if_blocks(blocks, None, branch='standalone')`), which is the call that does dispatch
child regions, and the census shows this loop owns exactly those children
(`IfRegion IF_THEN cond=@150..184 merge=@296`, `IfRegion IF_ELIF_CHAIN cond=@318..338 merge=@830`).

Join predicate (same as C): the conditional jump's landing block `_else_succ` is entered from
inside the then side as well (`@830` predecessors {@46 the cond block, @720, @722}), so it is the
`if`'s merge rather than an exclusive else arm. Then:
  * then suite = the loop's declared `body_blocks` minus the header block and minus the merge,
    rendered by `_if_generate_branch_stmts` - declared region data, no new membership invented;
  * `If(test=_expr, body=<then suite>)` with NO orelse, matching the compiled-shape signature
    proved by `compile()` (one top `POP_JUMP_FORWARD_IF_FALSE`, no bottom re-test, no tail);
  * the merge block rendered immediately after the If, i.e. `time.sleep(0.5)` inside the loop and
    after the if, which is the original's position (`@830` follows the then arm's fall-through).

usage: python -X utf8 build_cand_r36_R21-33c2_branch_suite.py <region_ast_generator.py>
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
    "                    # [R21-33c2] 落点块另有 from-then-侧 的前驱 => 它是本 if 的汇合点。",
    "                    # then 侧用循环体同款套件渲染器（会分发嵌套区域），汇合块紧随 If 之后。",
    "                    _r33c_loop = self._current_loop",
    "                    _r33c_join = (_then_succ is not None and _r33c_loop is not None",
    "                                  and getattr(_r33c_loop, 'body_blocks', None)",
    "                                  and any(p is not block and p is not _else_succ",
    "                                          and p.start_offset >= _then_succ.start_offset",
    "                                          for p in _else_succ.predecessors))",
    "                    if _r33c_join:",
    "                        _r33c_then_blocks = [b for b in _r33c_loop.body_blocks",
    "                                             if b is not block and b is not _else_succ",
    "                                             and b not in self.generated_blocks]",
    "                        _r33c_then_stmts = (self._if_generate_branch_stmts(",
    "                            blocks=_r33c_then_blocks) if _r33c_then_blocks else [])",
    "                        if _r33c_then_stmts:",
    "                            for _r33c_b in _r33c_then_blocks:",
    "                                self.generated_blocks.add(_r33c_b)",
    "                                self.generated_offsets.add(_r33c_b.start_offset)",
    "                            _hdr_stmts.append({'type': 'If', 'test': _expr,",
    "                                               'body': _r33c_then_stmts})",
    "                            _r33c_join_stmts = self._if_generate_branch_stmts(",
    "                                blocks=[_else_succ])",
    "                            if _r33c_join_stmts:",
    "                                _hdr_stmts.extend(_r33c_join_stmts)",
    "                                self.generated_blocks.add(_else_succ)",
    "                                self.generated_offsets.add(_else_succ.start_offset)",
    "                            return",
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
