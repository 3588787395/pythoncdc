# -*- coding: utf-8 -*-
"""emit_spec: build a diag4 candidate spec by extracting the EXACT landed bytes
(LF-normalised) around the [R64-diag1] pop site, so the anchor is guaranteed unique.

usage: python -X utf8 emit_spec.py <outspec.json> <variant>
Reads repo core read-only; writes only into D:/Temp/opencode/r65gate/diag4/specs/.
"""
import io
import json
import sys

REPO = r'F:/Downloads/pythoncdc-main'
REL = 'core/cfg/region_analyzer.py'


def landed_lf():
    s = io.open(REPO + '/' + REL, encoding='utf-8', newline='').read()
    return s.replace('\r\n', '\n')


def build(variant):
    u = landed_lf()
    anchor = """                    _r64_cj = (self.cfg.get_block_by_offset(last.argval)
                               if getattr(last, 'argval', None) is not None
                               else None)
                    if (_r64_closed and _r64_cj is not _r64_T
                            and ft_succ is not _r64_T):
                        chain.pop()
                        break
"""
    assert u.count(anchor) == 1, ('anchor count', u.count(anchor))
    common = """                    _r64_cj = (self.cfg.get_block_by_offset(last.argval)
                               if getattr(last, 'argval', None) is not None
                               else None)
"""
    if variant == 'n1':
        tail = """                    # [R65-diag4 n1 operand-rejoin exemption] Same-level structural
                    # identity for the short-circuit run: current is still a MEMBER of
                    # this operator run whenever one of its own two edges reaches the
                    # run's shared target T within one conditional hop -- either
                    # directly (already covered above) or through its successor block's
                    # own short-circuit edge.  That is exactly the lowering of
                    # `A or B or (C and D):` (De Morgan-guard shape): C is the head of
                    # the run's last operand, D's short-circuit edge jumps to T, and C's
                    # other edge is the run's negative exit.  In that case the run has
                    # NOT closed at T, so the pop must not fire.
                    # 识别条件：chain 前缀已全部汇入 T，但 current 的某条后继边（ft_succ 或
                    # _r64_cj）自身末指令是短路/条件跳转且落到 T。
                    # 归约方式：current（连同其后继）保留为本 BoolOp run 的操作数，chain 不弹出，
                    # walk 继续；BoolOpRegion 的 op_chain 覆盖 A、B、(C and D)。
                    # AST 映射：BoolOp(or, [A, B, BoolOp(and, [C, D])]) →
                    # `if A or B or (C and D): body`，而不是将 current 拆成下一条语句的 IfRegion
                    # （拆开会把 C 的极性翻转并把 D 变成孤块）。
                    _r64_rejoin = False
                    for _r64_s in (ft_succ, _r64_cj):
                        if _r64_s is None:
                            continue
                        _r64_sl = _r64_s.get_last_instruction()
                        if (_r64_sl is not None
                                and _r64_sl.opname in BOOLOP_CHAIN_JUMPS
                                and getattr(_r64_sl, 'argval', None) is not None
                                and self.cfg.get_block_by_offset(_r64_sl.argval) is _r64_T):
                            _r64_rejoin = True
                            break
                    if (_r64_closed and _r64_cj is not _r64_T
                            and ft_succ is not _r64_T
                            and not _r64_rejoin):
                        chain.pop()
                        break
"""
    elif variant == 'n2':
        # literal reading of the hand-off hint: do not pop when the popped block is
        # itself the FIRST block of the operator run (chain length 1 -> nothing to pop)
        # generalised to: do not pop when current == chain[0][0] OR the remaining chain
        # after the pop would no longer share the run head's op kind.
        tail = """                    # [R65-diag4 n2 run-head-exemption] literal hand-off reading: the
                    # popped block is the run head itself -> the run has only one
                    # operand left, so the pop destroys the run instead of closing it.
                    if (_r64_closed and _r64_cj is not _r64_T
                            and ft_succ is not _r64_T
                            and current is not chain[0][0]
                            and len(chain) > 3):
                        chain.pop()
                        break
"""
    else:
        raise SystemExit('unknown variant ' + variant)
    repl = common + tail
    return REL, [{'anchor': anchor, 'repl': repl}]


if __name__ == '__main__':
    out, variant = sys.argv[1], sys.argv[2]
    rel, edits = build(variant)
    io.open(out, 'w', encoding='utf-8', newline='').write(
        json.dumps({'file': rel, 'edits': edits}, ensure_ascii=False, indent=1))
    print('wrote', out, 'variant', variant, 'added lines',
          sum(e['repl'].count('\n') - e['anchor'].count('\n') for e in edits))
