"""R21-41: a back edge whose operand lands on the header IS the implicit tail — do not add a Continue.

Named cause (tasks.md §49, read off the generated source and settled by a compile() experiment):
the 40d product ends `_process_cancel_order`'s loop body with

```
574          time.sleep(0.001)
575          continue            ← spurious
```

and CPython 3.11 distinguishes the two shapes only by the jump TARGET:

```
S1 while True + terminal explicit continue :  backwards = [(60 → 2 = entry NOP), (118 → 4 = NOP+2)]
S2 while True, body simply ends            :  backwards = [(88 → 4)]
S3 tested while                           :  no entry NOP at all
```

The original is the S1 pattern only for its *explicit* continues (@44); its body tail lands on @46 =
NOP+2 = the body start, i.e. the S2/implicit form. Our extra `continue` replaces that single implicit
jump with a continue jump — same instruction count (which is why allwin/unit_diff read `hunks=0`),
different target, different CFG ⇒ judge *Different control flow*.

The emitter is `[R8 fix]` at region_ast_generator.py:27286-27294: it appends a Continue exactly when the
block's backward operand lands on `self._current_loop.header_block`. Its stated premise — "a
LOOP_BACK_EDGE block that carries user instructions must be an explicit continue" — was written while
`back_edge_block` was elected by payload size (see the [R21-40] analyzer census), so a payload-carrying
block designated as the back edge really was a continue block. After the analyzer fix, `back_edge_block`
means "the block whose operand lands on the header", which by definition is the natural tail, so the
premise inverts and the rule now manufactures the spurious Continue.

Hunk E1 therefore keys the emission on the shape the comment actually cares about — an *explicit*
continue lands on the loop's pure-noise re-entry block (a predecessor of the header that carries no user
instruction and has the header as its only successor), never on the header itself. Hunk E2 applies the
same discriminator inside the [R21-40d] shared-predecessor clause, which was the part that over-fired
into `ipo_stocks_order` (broker 125 → 124/128): a block entered by several arms may be claimed as a
shared chain tail only when it is a continue re-entry edge, keeping the landed arm-privacy requirement
for anything that lands on the header.

Both hunks read block structure and opcode class only: no names, no offsets, no counters, no thresholds.

usage: python -X utf8 build_cand_r38_R21-41_tail_continue.py <generator-file>   # base c1eba55fb9900412
"""
import hashlib
import py_compile
import sys

NOISE = "('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG', 'END_ASYNC_FOR')"

OLD_E1 = [
    "                            _loop_hdr = self._current_loop.header_block",
    "                            if _loop_hdr and _be_last2.argval is not None:",
    "                                _be_target = self.cfg.get_block_by_offset(_be_last2.argval)",
    "                                if _be_target and _be_target == _loop_hdr:",
    "                                    stmts.append({'type': 'Continue'})",
]

NEW_E1 = [
    "                            _loop_hdr = self._current_loop.header_block",
    "                            if _loop_hdr and _be_last2.argval is not None:",
    "                                _be_target = self.cfg.get_block_by_offset(_be_last2.argval)",
    "                                # [R21-41] 落点在 header 本身 = 循环体的隐含回边，循环结构已经发射这条",
    "                                # JUMP_BACKWARD，补 Continue 会把同一条跳转的落点从 header 改成 header 之前的",
    "                                # continue 再入块（指令条数不变、跳转目标变，judge 读作控制流不同——实测",
    "                                # _process_cancel_order 的 333/333 parity 残差就是这一条）。只有当落点是",
    "                                # 「header 之前、不含任何用户指令、唯一后继即 header」的纯噪声再入块时，",
    "                                # 这条后向跳转才是源码级 continue，需要显式发射。",
    "                                if (_be_target and _be_target is not _loop_hdr",
    "                                        and getattr(_be_target, 'instructions', None)",
    "                                        and all(i.opname in ("
    + NOISE + ") for i in _be_target.instructions)",
    "                                        and len(_be_target.successors) == 1",
    "                                        and _loop_hdr in _be_target.successors):",
    "                                    stmts.append({'type': 'Continue'})",
]

OLD_E2 = [
    "                        and _r39_Tpreds",
    "                        and _r39_tail in _r39_Tpreds",
    "                        and all(_r40d_p is _r39_tail or _r40d_p in _r40d_regblocks",
    "                                for _r40d_p in _r39_Tpreds)",
]

NEW_E2 = [
    "                        and _r39_Tpreds",
    "                        and _r39_tail in _r39_Tpreds",
    "                        # [R21-41] 多个前驱共享的链尾只在 continue 再入边上才可认领；落点即 header 的自然",
    "                        # 回边仍须保持 [R39-B] 原来的臂私有（len==1），否则会把循环自己的尾块当成某个臂的",
    "                        # continue 抢走（实测在 ipo_stocks_order 上过度发射，broker 125 → 124/128）。",
    "                        and (len(_r39_Tpreds) == 1 or _r40d_reentry)",
    "                        and all(_r40d_p is _r39_tail or _r40d_p in _r40d_regblocks",
    "                                for _r40d_p in _r39_Tpreds)",
]


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def splice(lines, old, new, tag):
    ob = [x.encode('utf-8') for x in old]
    hits = [n for n in range(len(lines) - len(ob) + 1) if lines[n:n + len(ob)] == ob]
    assert len(hits) == 1, '%s: anchor hits %d' % (tag, len(hits))
    n = hits[0]
    return lines[:n] + [x.encode('utf-8') for x in new] + lines[n + len(old):]


def main():
    target = sys.argv[1]
    raw = open(target, 'rb').read()
    pre = sha16(raw)
    assert raw.startswith(b'\xef\xbb\xbf'), 'expected BOM'
    assert raw.count(b'\n') == raw.count(b'\r\n'), 'mixed newlines - refuse'
    lines = raw.split(b'\r\n')
    assert b'[R21-40d]' in raw, 'base lacks the 40d hunks (expected c1eba55fb9900412)'
    lines = splice(lines, OLD_E2, NEW_E2, 'E2 (shared-pred clause)')
    lines = splice(lines, OLD_E1, NEW_E1, 'E1 ([R8 fix] emission)')
    patched = b'\r\n'.join(lines)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('size=%d sha16=%s (was %s) py_compile=OK' % (len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
