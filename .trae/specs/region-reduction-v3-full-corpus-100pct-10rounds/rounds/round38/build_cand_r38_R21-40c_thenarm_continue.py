"""R21-40c: hand [R21-35a]'s trailing Continue to the enclosing then-arm instead of the Try body tail.

The conjunct probe (r39b_probe.log, 247 records over the broker regen, mirror-only, mirror restored
and cmp-proved afterwards) settles the placement question with measured facts:

    [R39BPROBE] T@1822 tail=1712 Tgen=False Tinblocks=False Tinreg=False Tinbe=False
                Tpreds=[1710, 1712] pay=['JUMP_BACKWARD'] Llast=POP_TOP
                Tlast=JUMP_BACKWARD land=44 hdr=46 reentry=True

so the pure-continue block @1822 is reachable, is not the loop's back edge, its payload is exactly one
backward jump, and its landing IS the pure-noise continue re-entry block (which my [R21-40] analyzer
hunk and the 40b widening both read correctly) — but it has **two** predecessors (@1710 and @1712), so
the landed rule's arm-privacy conjunct `len(_r39_Tpreds) == 1` legitimately refuses it. That is not a
defect of the rule: a block entered by two arms of the same chain is the chain's *shared* tail, which
in the source sits after the chain, not inside one arm. The original's layout says the same thing:
@1822 (JUMP_BACKWARD -> @44, the continue) is followed by a separate @1826 (JUMP_FORWARD -> @2000)
block, which is the try body's normal-completion landing entered from the `if business_type in
('future','rzrq')` **false** side.

Consequence for [R21-35a], which produced the measured `delta=-1 hunks=1` state: it appends Continue to
`body_stmts` = the Try body tail, so the `business_type in (...)` false path also continues and the
body's normal-completion edge @1826 disappears (it cannot be emitted — there is no fall-through left).
The source shape the bytecode describes is one level in:

    if self.business_type in ('future', 'rzrq'):
        if error_no == 0: ...
        elif error_no == T2SDK_RTNPACK_EMPTY and node_type == '7': pass
        else: strategy_log.error(...)
        continue                       # <- shared chain tail, inside the then arm

Fix (this hunk): keep 35a's claim and bookkeeping exactly as they are, and place the Continue into the
then-suite of the statement the body ends with, but only when that statement is an `If` **without an
`orelse`** — the structural signature of "the chain's shared tail sits inside that arm". Anything else
falls back to the previous append, so the hunk is a strict refinement of already-fired behaviour.
No names, offsets, counters or thresholds.

usage: python -X utf8 build_cand_r38_R21-40c_thenarm_continue.py <generator-file>   # base a8155727b47e3bea
"""
import hashlib
import py_compile
import sys

OLD = [
    "                    body_stmts.append({'type': 'Continue'})",
    "                    self.generated_blocks.add(_r35_b)",
]

NEW = [
    "                    # [R21-40c] 实测：该纯回边块 @1822 的前驱是同一链的两个臂块（@1710 与 @1712），",
    "                    # 说明源码里这条 continue 是「链的公共尾」，位于外层 if 的 then 臂之内、链之后；",
    "                    # 把它挂在 try 体尾会让外层 if 的 false 侧也回边（实测抹掉 @1826 JUMP_FORWARD）。",
    "                    # 结构签名：try 体最后一条语句是一个没有 orelse 的 If ⇒ Continue 归它的 body。",
    "                    _r40c_last = body_stmts[-1] if body_stmts else None",
    "                    if (isinstance(_r40c_last, dict) and _r40c_last.get('type') == 'If'",
    "                            and not _r40c_last.get('orelse')",
    "                            and isinstance(_r40c_last.get('body'), list)):",
    "                        _r40c_last['body'].append({'type': 'Continue'})",
    "                    else:",
    "                        body_stmts.append({'type': 'Continue'})",
    "                    self.generated_blocks.add(_r35_b)",
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
    assert len(hits) == 1, 'anchor hits %d (the [R21-35a] claim must be unique)' % len(hits)
    n = hits[0]
    assert b'_r35_pay' in b'\r\n'.join(lines[max(0, n - 30):n]), 'anchor not inside the [R21-35] claim'
    out = lines[:n] + [x.encode('utf-8') for x in NEW] + lines[n + len(OLD):]
    patched = b'\r\n'.join(out)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('replaced %d with %d lines at :%d size=%d sha16=%s (was %s) py_compile=OK'
          % (len(OLD), len(NEW), n + 1, len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
