"""R37 candidate builder (R21-35): a back-edge block that sits inside the try's declared protected
span belongs to the try BODY, not to the parent suite.

Measured cause (trade_live_broker._process_cancel_order, `len orig=333 prod=332 delta=-1 hunks=3`):
the original ends the inner try's body with `continue`, so CPython lays out
`@1820 POP_TOP / @1822 EXTENDED_ARG / @1824 JUMP_BACKWARD->44 / @1826 JUMP_FORWARD->2000(handler
skip) / @1828 PUSH_EXC_INFO …`, while our product renders `except …: …` and only THEN the
`continue`, giving `@1822 JUMP_FORWARD->1926 / @1824 PUSH_EXC_INFO … / @1928 JUMP_BACKWARD->44` -
one instruction short and semantically different (after an exception our version jumps to the loop
top instead of falling through to the trailing `time.sleep(0.001)`). Decided by compiling both
source shapes on 3.11.7 (`rounds/round37/shape_battery_r37.py` row C: `len 53/53` with exactly ONE
positional diff, JUMP_BACKWARD -> JUMP_FORWARD; the 164-vs-163 pair is in `FIX_R21-33_r36.md`'s
companion rig), so the fix is placement, not a jump-operand question.

Data used is the region's own declaration: the analyzer already publishes the protected span, and
the continue block here starts exactly AT `try_offset_end` (@1822 with `try_offset_end=1822`),
i.e. inside the span, while `try_blocks` (which the body walk uses) does not contain it. Predicate
at the end of `_generate_try_body`: a successor of a try block that (1) is owned by no part of this
region (blocks/try_blocks/handler bodies/cleanup), (2) is not already generated, (3) starts no
later than `try_offset_end`, (4) whose entire payload is ONE backward jump (after dropping
RESUME/NOP/CACHE/EXTENDED_ARG noise), and (5) whose target lies at or before the try's own start
while a loop is the current emission context. Then the `continue` is appended to the body and the
block is registered as generated so the parent suite does not also emit it.

usage: python -X utf8 build_cand_r37_R21-35_trybody_continue.py <region_ast_generator.py>
"""
import hashlib
import py_compile
import sys

NOISE_LINE = "    # [W13] finally 双副本 return 形态的框架操作码：SWAP/POP_TOP/COPY 为纯栈"

OLD = [
    "                for b in ntr.blocks:",
    "                    self.generated_blocks.add(b)",
    "",
    "        return body_stmts",
]

NEW = [
    "                for b in ntr.blocks:",
    "                    self.generated_blocks.add(b)",
    "",
    "        # [R21-35] 保护跨度内的纯回边块属于 try 体的最后一条 continue，不属父序列。",
    "        # 判据只用区域自己声明的数据 + 块自身的指令载荷，无名字/偏移常量/计数阈值：",
    "        #   ①本块是本 region try_blocks 某块的后继；",
    "        #   ②不被本 region 任何部分（blocks/try_blocks/handler body/cleanup）持有，",
    "        #     且尚未生成；",
    "        #   ③起点不晚于本 region 声明的 try_offset_end（仍在保护跨度内）；",
    "        #   ④丢掉 RESUME/NOP/CACHE/EXTENDED_ARG 噪声后只剩一条向后跳转；",
    "        #   ⑤跳转落点不在 try 体之后（≤ 本 try 的 try_offset_start），且当前正在",
    "        #     装配某个循环（回边语义由所属循环给出，不比较具体偏移值）。",
    "        _r35_span_end = getattr(region, 'try_offset_end', None)",
    "        _r35_span_start = getattr(region, 'try_offset_start', None)",
    "        if (_r35_span_end is not None and _r35_span_start is not None",
    "                and self._current_loop is not None",
    "                and getattr(region, 'except_handlers', None)):",
    "            _r35_owned = set(region.blocks or ()) | set(region.try_blocks or ())",
    "            for _r35_t, _r35_n, _r35_hb in region.except_handlers:",
    "                _r35_owned.update(_r35_hb or [])",
    "            _r35_owned.update(getattr(region, 'cleanup_blocks', None) or [])",
    "            _r35_noise = ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG')",
    "            _r35_added = False",
    "            for _r35_src in (region.try_blocks or []):",
    "                for _r35_b in (getattr(_r35_src, 'successors', None) or []):",
    "                    if _r35_b in _r35_owned or _r35_b in self.generated_blocks:",
    "                        continue",
    "                    if _r35_b.start_offset > _r35_span_end:",
    "                        continue",
    "                    _r35_pay = [i for i in _r35_b.instructions",
    "                                if i.opname not in _r35_noise]",
    "                    if len(_r35_pay) != 1:",
    "                        continue",
    "                    if not _r35_pay[0].opname.startswith('JUMP_BACKWARD'):",
    "                        continue",
    "                    _r35_tgt = (self.cfg.get_block_by_offset(_r35_pay[0].argval)",
    "                                if _r35_pay[0].argval is not None else None)",
    "                    if _r35_tgt is None or _r35_tgt.start_offset > _r35_span_start:",
    "                        continue",
    "                    body_stmts.append({'type': 'Continue'})",
    "                    self.generated_blocks.add(_r35_b)",
    "                    self.generated_offsets.add(_r35_b.start_offset)",
    "                    _r35_added = True",
    "                    break",
    "                if _r35_added:",
    "                    break",
    "",
    "        return body_stmts",
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
    assert len(hits) == 1, 'anchor hits %d (the _generate_try_body tail must be unique)' % len(hits)
    n = hits[0]
    ctx = b'\r\n'.join(lines[max(0, n - 1400):n])
    assert b'def _generate_try_body' in ctx, 'anchor not inside _generate_try_body'
    assert b'_ntr' in ctx, 'anchor not at the nested-try tail'
    out = lines[:n] + [x.encode('utf-8') for x in NEW] + lines[n + len(ob):]
    patched = b'\r\n'.join(out)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('replaced %d lines with %d at :%d size=%d sha16=%s (was %s) py_compile=OK'
          % (len(OLD), len(NEW), n + 1, len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
