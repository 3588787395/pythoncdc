"""R36 candidate builder (R21-33 hunk B): a header-block test whose landing block jumps back
to that same header is not a loop exit, so the loop is `while True` and the test is an inner if.

Measured on the gate-35 sealed base (trade_live_broker._trade_status_handle, census
D:/Temp/r36/region_census_r36b.py): LoopRegion header=cond=@46..@148 (20 instructions),
is_while_true=False, metadata is_degenerate_while=True, else_blocks=[@720, @830],
back_edge_block=@830. Block @46 ends `POP_JUMP_FORWARD_IF_FALSE -> 830`; block @830
(`time.sleep(0.5)` + `JUMP_BACKWARD -> 46`) has predecessors {@46, @720, @722}. So BOTH exits of
the header's conditional jump stay inside the cycle: the false edge lands on a block whose very
next instruction re-enters the header, and the fall-through path reaches the same block. A
`while cond:` cannot be left this way - the only real exit of the loop is `RETURN_VALUE` @450 -
so the region is a `while True:` whose header block carries a nested `if`, and declaring @830 as
`else_blocks` makes the generator emit a while/else, which CPython 3.11 compiles with the test
TWICE (top POP_JUMP_FORWARD_IF_FALSE + bottom POP_JUMP_BACKWARD_IF_TRUE, measured shape dump
D:/Temp/r36/shape_tails2.py: S2 = 109 instructions with a bottom re-test and a trailing
LOAD_CONST None/RETURN_VALUE, S1 = the original's signature: NOP continue target, single top
test, unconditional JUMP_BACKWARD to the body start, no tail).

The predicate reads only the header's own data (its conditional jump operand and that target
block's last instruction), i.e. opcode-class/edge shape, no names, offsets or counters, and it
runs at identification time inside _is_while_true, not as a retrospective repair.

usage: python -X utf8 build_cand_r36_R21-33b_while_true.py <region_analyzer.py>
"""
import hashlib
import py_compile
import sys

OLD = [
    "        if cond_jump_instr is not None and cond_jump_instr.argval is not None:",
    "            jump_target = self.cfg.get_block_by_offset(cond_jump_instr.argval)",
    "            if jump_target is not None and jump_target == header:",
]

NEW = [
    "        if cond_jump_instr is not None and cond_jump_instr.argval is not None:",
    "            jump_target = self.cfg.get_block_by_offset(cond_jump_instr.argval)",
    "            # [R21-33b] 区域识别原则 1（自底向上）+ 判据只看自身边形状：header 块尾条件跳转的",
    "            # 落点若以回到本 header 的后边跳转结束，则该条件不是循环出口——两条路都留在环内，",
    "            # 循环本体只能是 while True，块尾条件是本体内嵌套的 if（_trade_status_handle 实测",
    "            # @46 POP_JUMP_FORWARD_IF_FALSE→@830，@830 末条 JUMP_BACKWARD→@46，@830 前驱",
    "            # {@46,@720,@722}）。误判成 while cond + else 会让 CPython 3.11 把条件编译两遍",
    "            # （顶部 POP_JUMP_FORWARD_IF_FALSE + 底部 POP_JUMP_BACKWARD_IF_TRUE）并在函数尾",
    "            # 追加 LOAD_CONST None/RETURN_VALUE，替换掉原有的无条件回边。",
    "            if (jump_target is not None and jump_target is not header",
    "                    and jump_target.instructions):",
    "                _r33_back = jump_target.instructions[-1]",
    "                if (_r33_back.opname.startswith('JUMP_BACKWARD')",
    "                        and _r33_back.argval is not None",
    "                        and self.cfg.get_block_by_offset(_r33_back.argval) == header):",
    "                    return True",
    "            if jump_target is not None and jump_target == header:",
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
    assert len(hits) == 1, 'anchor hits %d (_is_while_true jump-target branch must be unique)' % len(hits)
    n = hits[0]
    ctx = b'\r\n'.join(lines[max(0, n - 40):n])
    assert b'def _is_while_true' in ctx, 'anchor not inside _is_while_true'
    out = lines[:n] + [x.encode('utf-8') for x in NEW] + lines[n + len(ob):]
    patched = b'\r\n'.join(out)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('replaced %d lines with %d at :%d size=%d sha16=%s (was %s) py_compile=OK'
          % (len(OLD), len(NEW), n + 1, len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
