"""R21-40b: let the landed arm-tail-continue rule [R39-B] see CPython 3.11's continue re-entry block.

Measured chain on trade_live_broker._process_cancel_order (allwin_r63.py windows, same judge):
  landed                              delta=-1 hunks=3
  + [R21-35a] generator               delta=-2 hunks=2
  + [R21-40]  analyzer only           delta= 0 hunks=2
  + both halves (the pair)            delta=-1 hunks=1   <- only @1826 JUMP_FORWARD missing
The surviving window is the `try` body's normal-completion edge, and the reason no rule can give the
inner `else` arm its own `continue` is now measured (probe, read-only, on landed bytes): the block that
carries it is `@1822..@1824 = [EXTENDED_ARG, JUMP_BACKWARD -> @44]`, role CONTINUE, owner LoopRegion@46.
The landed [R39-B] arm-tail rule (region_ast_generator.py:27800-27852) rejects it on TWO conjuncts:
  * `len(list(T.instructions)) == 1` counts the EXTENDED_ARG prefix, although this very file treats
    EXTENDED_ARG as noise everywhere else (:27226-27237 "全库既定噪声，见 W14 修复", and [R21-35a]'s own
    `_r35_noise` tuple), and jump offsets >= 256 instructions always carry one;
  * `get_block_by_offset(Tlast.argval) is _r39_hdr` demands the operand land on the header, but
    CPython 3.11 compiles an explicit `continue` to the loop's **pre-header pure-noise re-entry block**
    (@44 = a 1-instruction NOP whose only successor is the header @46) and only the *implicit* body-tail
    back edge lands on the header. That distinction is precisely what the [R21-40] analyzer hunk uses to
    tell a `continue` back edge from the natural one, so this file now reads the same structural fact.
Both changes are refinements of conjuncts that already exist, using the file's own conventions; no
names, offsets, counters or thresholds are introduced, and everything else about the rule is untouched
(arm-private predecessor, not the loop's designated back edge, tail block ends without a jump).

usage: python -X utf8 build_cand_r38_R21-40b_r39b_reentry.py <generator-file>
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
    "                # [R21-40b] 两条修正都用本文件既定约定，不新增判据：",
    "                # ①载荷长度剔除噪声（RESUME/NOP/CACHE/EXTENDED_ARG）——EXTENDED_ARG 是全库既定噪声",
    "                #   （见上方 :27226 R68-b3 注释与本规则自己跳过的噪声），而跳转距离 ≥256 指令时",
    "                #   CPython 必然在 JUMP_BACKWARD 前插一条 EXTENDED_ARG，原来的 len(...)==1 于是",
    "                #   把所有大循环里的纯 continue 块排除在外（实测 @1822..@1824 即 [EXTENDED_ARG, JUMP_BACKWARD]）。",
    "                # ②落点允许「header 之前的纯噪声再入块」：CPython 3.11 把显式 continue 编译到该块，",
    "                #   只有循环体的隐含回落才直接落 header。这正是 [R21-40] 在分析层区分两种回边用的",
    "                #   同一个结构事实（纯噪声、单后继、后继即 header）。",
    "                _r39_Tpay = [i for i in (getattr(_r39_T, 'instructions', None) or [])",
    "                             if i.opname not in ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG')]",
    "                _r39_Tland = (self.cfg.get_block_by_offset(_r39_Tlast.argval)",
    "                              if (_r39_Tlast is not None and isinstance(_r39_Tlast.argval, int))",
    "                              else None)",
    "                _r39_reentry = (_r39_Tland is not None and _r39_Tland is not _r39_hdr",
    "                                and getattr(_r39_Tland, 'instructions', None)",
    "                                and _r39_Tland.start_offset < _r39_hdr.start_offset",
    "                                and all(i.opname in ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG')",
    "                                        for i in _r39_Tland.instructions)",
    "                                and len(_r39_Tland.successors) == 1",
    "                                and _r39_hdr in _r39_Tland.successors)",
    "                if (_r39_T not in self.generated_blocks",
    "                        and _r39_T not in list(blocks)",
    "                        and _r39_T not in (getattr(region, 'blocks', None) or set())",
    "                        and _r39_T not in _r39_be",
    "                        and len(_r39_Tpreds) == 1",
    "                        and _r39_Tpreds[0] is _r39_tail",
    "                        and len(_r39_Tpay) == 1",
    "                        and _r39_Llast is not None",
    "                        and 'JUMP' not in _r39_Llast.opname",
    "                        and _r39_Tlast is not None",
    "                        and _r39_Tlast.opname in ('JUMP_BACKWARD',",
    "                                                  'JUMP_BACKWARD_NO_INTERRUPT')",
    "                        and isinstance(_r39_Tlast.argval, int)",
    "                        and (_r39_Tland is _r39_hdr or _r39_reentry)):",
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
    assert len(hits) == 1, 'anchor hits %d (the [R39-B] condition must be found exactly once)' % len(hits)
    n = hits[0]
    ctx = b'\r\n'.join(lines[max(0, n - 45):n])
    assert b'[R39-B]' in ctx, 'anchor is not inside the [R39-B] arm-tail rule'
    out = lines[:n] + [x.encode('utf-8') for x in NEW] + lines[n + len(OLD):]
    patched = b'\r\n'.join(out)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('replaced %d with %d lines at :%d size=%d sha16=%s (was %s) py_compile=OK'
          % (len(OLD), len(NEW), n + 1, len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
