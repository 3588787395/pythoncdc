"""R39/R21-40 candidate builder: exclude continue-re-entry back edges when the header carries the test.

MEASURED DEFECT (census_backedge_r38.py + probe_r39b_r38.py, read-only, on landed bytes):
`region_analyzer.py:4958` collects `back_edges_for_header` from `loop_analyzer.back_edges` keyed by the
loop's theoretical back edges, so a source-level `continue` whose operand lands on CPython 3.11's
pure-noise pre-header re-entry block (the `while` loop's NOP) is in the same pool as the loop's natural
body tail. The exclusion that recognises that re-entry block lives behind the guard
`if condition_block == header:` (:4960), and `_process_cancel_order`'s loop declares
`condition_block is None` while its header block @46 IS the test (`LOAD_GLOBAL … POP_JUMP_FORWARD_IF_FALSE`)
— so the guard is skipped and the selection key at :4992, which prefers the block with MORE body
instructions, picks `@1930..@1998` (an `else: stmt; continue` arm, 11 instructions, operand → @44 the
NOP) over the true body tail `@2000..@2042` (the `time.sleep(0.001)` statement, operand → @46 = the
header). The consequences are exactly the two windows measured on the panel product:
`_process_cancel_order delta=-1 hunks=3` — the arm's `continue` is never emitted, and the block that
IS the designated back edge is emitted as the loop's own tail.

Census over 11 of the 20 panel files (393 LoopRegions): 42 loops have a test-carrying header with
`condition_block is not header` (guard skipped), 67 designated back edges do not land on their header,
and 14 designations would move — among them `_process_order` (@360→@44, better @3128),
`_process_cancel_order` (@1930→@44, better @2000) and the currently-green `_trade_status_handle`
(@186→@44, better @830), which is why this goes through the 20-file panel before any gate.

Fix shape: purely additive, and the SAME predicate the landed guard already uses, evaluated only in the
case the landed guard misses. Inert when (a) the header is not the test carrier, (b) the header has no
pure-noise single-successor predecessor, or (c) no candidate is excluded (the filtered list is kept
only if non-empty). No names, no offsets, no counters, no thresholds.

usage: python -X utf8 build_cand_r38_R21-40_backedge_header.py <analyzer-file>
"""
import hashlib
import py_compile
import sys

OLD = [
    "            _else_blocks_set = set(else_blocks) if else_blocks else set()",
    "            if condition_block == header:",
]

NEW = [
    "            _else_blocks_set = set(else_blocks) if else_blocks else set()",
    "            # [R21-40] 上面的 :4960 守卫只在 condition_block 就是 header 时排除「continue 落点」回边块，",
    "            # 但本文件大量循环把条件求值放在 header 块里而 condition_block=None（实测 _process_cancel_order",
    "            # 的循环 header=@46，末指令 POP_JUMP_FORWARD_IF_FALSE，condition_block=None）。漏掉这一形态时，",
    "            # :4992 的选择键按「体内指令条数」排序，会把 `else: 语句; continue` 臂块（其回边操作数落在",
    "            # header 之前的纯噪声再入块 @44 上）选成循环的自然回边，真正的循环尾（操作数正好落在 header 上）",
    "            # 反被标成 CONTINUE ⇒ 臂尾的 continue 无人发射。",
    "            # 判据与 :4961-4966 逐字相同（header 的纯噪声单后继前驱 = CPython 的 continue 再入块），只是把",
    "            # 它补到被漏掉的那一形态上；此处不新增谓词，也不读名字/偏移/计数阈值。",
    "            # 保守性：header 末指令不是条件跳转、再入块集合为空、或过滤后候选为空时一律不改",
    "            # back_edges_for_header ⇒ 与修改前逐字节相同。",
    "            _r40_hdr_last = header.get_last_instruction()",
    "            if (condition_block is not header and back_edges_for_header and _r40_hdr_last is not None",
    "                    and _r40_hdr_last.opname in FORWARD_CONDITIONAL_JUMP_OPS):",
    "                _r40_ph_set = set()",
    "                for _r40_ph in header.predecessors:",
    "                    if (_r40_ph.start_offset < header.start_offset",
    "                            and all(i.opname in NOISE_OPS for i in _r40_ph.instructions)",
    "                            and len(_r40_ph.successors) == 1 and header in _r40_ph.successors):",
    "                        _r40_ph_set.add(_r40_ph)",
    "                if _r40_ph_set:",
    "                    _r40_kept = []",
    "                    for _r40_src in back_edges_for_header:",
    "                        _r40_last = _r40_src.get_last_instruction()",
    "                        if (_r40_last and _r40_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')):",
    "                            _r40_tgt = (self.cfg.get_block_by_offset(_r40_last.argval)",
    "                                        if _r40_last.argval is not None else None)",
    "                            if _r40_tgt in _r40_ph_set:",
    "                                continue",
    "                        _r40_kept.append(_r40_src)",
    "                    if _r40_kept:",
    "                        back_edges_for_header = _r40_kept",
    "            if condition_block == header:",
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
    assert len(hits) == 1, 'anchor hits %d (back-edge selection must be unique)' % len(hits)
    n = hits[0]
    ctx = b'\r\n'.join(lines[max(0, n - 20):n])
    assert b'back_edges_for_header = [src for src, tgt in self.loop_analyzer.back_edges' in ctx, \
        'anchor not in the back-edge selection'
    assert b'NOISE_OPS' in raw and b'FORWARD_CONDITIONAL_JUMP_OPS' in raw, 'constants missing'
    out = lines[:n] + [x.encode('utf-8') for x in NEW] + lines[n + len(OLD):]
    patched = b'\r\n'.join(out)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('replaced %d with %d lines at :%d size=%d sha16=%s (was %s) py_compile=OK'
          % (len(OLD), len(NEW), n + 1, len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
