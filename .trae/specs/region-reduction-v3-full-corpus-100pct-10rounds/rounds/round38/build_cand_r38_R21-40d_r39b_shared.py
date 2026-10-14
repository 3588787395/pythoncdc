"""R21-40d: [R39-B] widened for chain-shared continue blocks (noise payload, re-entry landing, shared preds).

Applied on top of 40c (`ccd97ff680b7434c`) and measured together with the analyzer hunk
`f7d849e974904492`. The 247-record conjunct probe (PROBE_R39B_conjuncts_sample.txt) says the landed
arm-tail rule reaches the continue block and is stopped by exactly three conjuncts, none of which
carries a name, offset or threshold:

  1. `len(list(T.instructions)) == 1` counts the `EXTENDED_ARG` prefix that CPython inserts for jump
     distances >= 256 instructions, although this file treats EXTENDED_ARG as noise in the very rules
     above (:27226-27237, "全库既定噪声，见 W14 修复") and in [R21-35a]'s own `_r35_noise` tuple;
  2. `get_block_by_offset(Tlast.argval) is _r39_hdr` demands a header landing, while 3.11 compiles an
     explicit `continue` onto the loop's pure-noise pre-header re-entry block (@44: one NOP, one
     successor = the header @46) and reserves the header landing for the implicit body tail — the same
     structural fact the [R21-40] analyzer hunk uses to tell the two back edges apart;
  3. `len(_r39_Tpreds) == 1 and _r39_Tpreds[0] is _r39_tail` demands arm privacy, but a `continue` that
     follows an if/elif/else chain is entered by EVERY arm that reaches the chain end (probe:
     `T@1822 Tpreds=[1710, 1712]` — the `pass` arm's jump and the else arm's fall-through), so the
     source statement is the chain's shared tail rather than one arm's terminator. The measured pair of
     placements proves the two are different rules: 40c puts that shared tail into the then-suite of the
     `If` the body ends with (restoring the body's normal-completion edge @1826) and leaves the OUTER
     chain's `@1998` unclaimed, while 35a's body-tail append claims @1998 and deletes @1826.

Relaxation 3 keeps the rule's intent: the block may be entered by several predecessors, but every one of
them must be a member of the SAME region being rendered (or the tail block itself), so a genuine
cross-region merge/join block is still refused — which is what the landed comment warns about
(merge-type successors must not be claimed, or the recompiled product gains a JUMP_BACKWARD).

Everything else is untouched: unclaimed, not in this arm's block list, not in the region's block set,
not the loop's designated back edge, exactly one non-noise payload instruction, the tail block ends
without a jump, and the landing is either the header or the pure-noise re-entry block.

usage: python -X utf8 build_cand_r38_R21-40d_r39b_shared.py <generator-file>   # base ccd97ff680b7434c
"""
import hashlib
import py_compile
import sys

OLD = [
    "                _r39_Tpreds = list(getattr(_r39_T, 'predecessors', None) or [])",
    "                if (_r39_T not in self.generated_blocks",
    "                        and _r39_T not in list(blocks)",
    "                        and _r39_T not in (getattr(region, 'blocks', None) or set())",
    "                        and _r39_T not in _r39_be",
    "                        and len(_r39_Tpreds) == 1",
    "                        and _r39_Tpreds[0] is _r39_tail",
    "                        and len(list(getattr(_r39_T, 'instructions', None) or [])) == 1",
    "                        and _r39_Llast is not None",
    "                        and 'JUMP' not in _r39_Llast.opname",
    "                        and _r39_Tlast is not None",
    "                        and _r39_Tlast.opname in ('JUMP_BACKWARD',",
    "                                                  'JUMP_BACKWARD_NO_INTERRUPT')",
    "                        and isinstance(_r39_Tlast.argval, int)",
    "                        and self.cfg.get_block_by_offset(_r39_Tlast.argval) is _r39_hdr):",
]

NEW = [
    "                _r39_Tpreds = list(getattr(_r39_T, 'predecessors', None) or [])",
    "                # [R21-40d] 三处放宽都用本文件既定约定，不引入名字/偏移/计数阈值：",
    "                # ①载荷剔除噪声（RESUME/NOP/CACHE/EXTENDED_ARG）——跳转距离 >=256 指令时 CPython 必插",
    "                #   EXTENDED_ARG，原 len(...)==1 于是排除了大循环里的纯 continue 块（实测 @1822..@1824 =",
    "                #   [EXTENDED_ARG, JUMP_BACKWARD]）。",
    "                # ②落点允许 header 之前的纯噪声再入块：CPython 3.11 把显式 continue 编译到该块，隐含的",
    "                #   体尾才直接落 header（与 [R21-40] 在分析层区分两种回边用的是同一个结构事实）。",
    "                # ③前驱允许多个，但必须全部属于正在归约的这个区域（或就是本臂尾块）——链尾的 continue 被",
    "                #   每个到达链尾的臂共享（实测 T@1822 Tpreds=[1710,1712]：pass 臂的跳转 + else 臂的直落），",
    "                #   而跨区域的汇合块仍然拒绝，正是原注释要求守住的那一类误认领。",
    "                _r40d_noise = ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG')",
    "                _r40d_pay = [i for i in (getattr(_r39_T, 'instructions', None) or [])",
    "                             if i.opname not in _r40d_noise]",
    "                _r40d_land = (self.cfg.get_block_by_offset(_r39_Tlast.argval)",
    "                              if (_r39_Tlast is not None and isinstance(_r39_Tlast.argval, int))",
    "                              else None)",
    "                _r40d_reentry = (_r40d_land is not None and _r40d_land is not _r39_hdr",
    "                                 and getattr(_r40d_land, 'instructions', None)",
    "                                 and _r40d_land.start_offset < _r39_hdr.start_offset",
    "                                 and all(i.opname in _r40d_noise for i in _r40d_land.instructions)",
    "                                 and len(_r40d_land.successors) == 1",
    "                                 and _r39_hdr in _r40d_land.successors)",
    "                _r40d_regblocks = getattr(region, 'blocks', None) or set()",
    "                if (_r39_T not in self.generated_blocks",
    "                        and _r39_T not in list(blocks)",
    "                        and _r39_T not in (getattr(region, 'blocks', None) or set())",
    "                        and _r39_T not in _r39_be",
    "                        and _r39_Tpreds",
    "                        and _r39_tail in _r39_Tpreds",
    "                        and all(_r40d_p is _r39_tail or _r40d_p in _r40d_regblocks",
    "                                for _r40d_p in _r39_Tpreds)",
    "                        and len(_r40d_pay) == 1",
    "                        and _r39_Llast is not None",
    "                        and 'JUMP' not in _r39_Llast.opname",
    "                        and _r39_Tlast is not None",
    "                        and _r39_Tlast.opname in ('JUMP_BACKWARD',",
    "                                                  'JUMP_BACKWARD_NO_INTERRUPT')",
    "                        and isinstance(_r39_Tlast.argval, int)",
    "                        and (_r40d_land is _r39_hdr or _r40d_reentry)):",
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
    assert len(hits) == 1, 'anchor hits %d (the [R39-B] condition must appear exactly once)' % len(hits)
    n = hits[0]
    assert b'[R39-B]' in b'\r\n'.join(lines[max(0, n - 45):n]), 'anchor not inside the [R39-B] rule'
    assert b'[R21-40c]' in b'\r\n'.join(lines), 'base lacks the 40c placement hunk'
    out = lines[:n] + [x.encode('utf-8') for x in NEW] + lines[n + len(OLD):]
    patched = b'\r\n'.join(out)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('replaced %d with %d lines at :%d size=%d sha16=%s (was %s) py_compile=OK'
          % (len(OLD), len(NEW), n + 1, len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
