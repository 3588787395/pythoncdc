# -*- coding: utf-8 -*-
"""rr-v5r192 patch: narrow the r143 [v143-ORCHAIN] while-or chain closure.

Single method, `core/cfg/region_analyzer.py::_detect_while_boolop_forward_chain`.

r143 closed the "while or chain dropped" family: for ``while A or B:`` the member
jumps structurally violate the R07 ``all_same_target`` test (the or-head's TRUE
jump goes to the body header, the tail's FALSE jump goes to the loop exit), so the
closure accepts the forward chain when
  (1) chain head op == 'or' and its jump target == loop.header_block,
  (2) last member ends in a FORWARD FALSE conditional jump whose target is the
      loop exit and is not part of the loop-body semantic set,
  (3) last member's fall-through == loop.header_block,
  (4) non-head members carry no STORE_*.

That premise silently assumes ``chain[0]`` is the *first* operand of the
condition.  The forward walk however starts at ``loop.condition_block``, and for a
rotated while the condition block can be a *middle* member - the boundary member
between an and-group and the or tail.  ``while a and b or c:`` compiles to
a: IF_FALSE -> c / b: IF_TRUE -> header / c: IF_FALSE -> exit, so the walk starts
at ``b``, collects ``[(b,'or'), (c,'and')]``, and criteria (1)-(4) all hold.  The
closure then returns half the condition; the earlier operand ``a`` is hoisted out
as an ``if a:`` guard, so the condition is truncated
(test_repros/round1/r1_10_while_mixed.pyc: ``while a and b or c:`` becomes
``if a: while b or c: ... if not a: break``, direct run 10 -> 0).

In that shape the chain head is entered from an earlier condition operand: an
external (non-loop-body) fall-through predecessor that ends in a FORWARD *FALSE*
conditional jump whose target is the chain's *last* member - the earlier operand
skips the whole or tail in one edge (the flat ``A and B or C`` shape, cf. the
contrast criterion of ``_detect_while_condition_nested_and_or_chain``: the
nested ``while A and (B or C):`` and-head jumps past the whole or run to the
false exit instead) - and whose other successor (the fall-through) is the chain
head.

Narrowing = one structural conjunct (no numbers, no names, no offsets): when such
a predecessor exists on the chain head, the closure may only keep its result if it
actually *prepended* that earlier and-group (the r144/r145/r146 prefix paths); an
unprefixed (truncated) chain is dropped instead, i.e. the method returns None
exactly as before r143 and the backward walk assembles the complete mixed chain
(``_detect_while_condition_boolop_chain`` fall-through), which is r142's output.
The accepted set is a strict subset of r143's; anything not matched keeps its
bytes (C3).  A genuine or-head chain has its head's predecessor false edge on the
loop exit / outside merge, not on the chain's last member (r143's E1/E2/E3 and the
difflib or chains keep the closure); the ``while A and (B or C):`` and-head
(v144/v145 prefix path) jumps past the whole or run to the false exit, so it is
not matched either; and a TRUE-polarity edge means a negated operand
(``while not A and B or C:``), a different family, also not matched.

Usage:
    python fix192.py            # apply (idempotent, skips an already-applied hunk)
    python fix192.py --revert   # revert to the pre-patch bytes
    python fix192.py --root DIR # patch the tree at DIR (default: the repo)
"""
import hashlib
import os
import py_compile
import sys
import tempfile

DEFAULT_ROOT = r'F:\Downloads\pythoncdc-main'
TARGET = os.path.join('core', 'cfg', 'region_analyzer.py')

HUNK_OLD = """        if all_same_target:
            return chain
        # [v143-ORCHAIN] or 链前向闭合（只增不破）：or 链（``while A or B:``）
"""

HUNK_NEW = """        if all_same_target:
            return chain
        # [v192-CHAINENTRY] 链首完整性收窄（只增不破）：v143 的 or 链闭合判据
        # 隐含假定 chain[0] 是条件表达式的**首**操作数，但前向走查自 loop.
        # condition_block 起步——旋转 while 的 condition_block 可能落在链的
        # **中间**成员（and 组与 or 尾的边界成员）。此时链首之前还有更早的
        # 操作数：该块以 FORWARD FALSE 族条件跳转收尾，假边**越过本链首直达
        # or 尾终成员**（== 本链末成员，即扁平 ``A and B or C`` 的「A 假边直
        # 达下一组求值起点」结构特征，与 _detect_while_condition_nested_and_
        # or_chain 的对照判据同源），落空续接链首。v143 闭合判据①②③④全部
        # 成立而误接受半条链 ⇒ 更早的操作数被外提成 ``if A:`` 守卫，条件被截
        # 短（r1_10 实测 ``while a and b or c:`` → ``if a: while b or c:``，
        # 直跑 10→0）。
        # 判据（I.4 白名单：块末 opcode 极性 + 跳转/落空目标同一性 + 块归属）：
        # 链首存在「非链成员、非循环体」的 fall-through 前驱，其条件跳转目标
        # == 本链**末**成员、且链首在其后继集合中 ⇒ 链首不是条件入口（更早的
        # 操作数把整条 or 尾一次跳过，or 尾仅该末成员待求值）。收尾处若闭合
        # 已把该 and 组前缀前置（v144/v145/v146 路径，链首完整性已由前置修
        # 复）则保留结果；仍为半条链时逐位落回 None，由后续后向走查装配完整
        # 混合链（= r142 行为）。真 or 首链（``while A or B:``）的链首前驱假
        # 边指向循环出口/循环外 merge，不在链末成员；``while A and (B or C):``
        # 的 and 头假边越过整个 or run 直达假出口，同样不命中；TRUE 极性边属
        # 取反操作数（``while not A and B or C:``）族，亦不命中。
        _oc_entry_skip = False
        _oc_prefixed = False
        if len(chain) >= 2 and chain[0][1] == 'or':
            _oc_member_offsets = {_oc_b.start_offset for _oc_b, _ in chain}
            _oc_tail_off = chain[-1][0].start_offset
            _oc_head = chain[0][0]
            for _oc_pp in _oc_head.predecessors:
                if _oc_pp.start_offset in _oc_member_offsets:
                    continue
                if _oc_pp in loop.blocks or _oc_pp in (loop.body_blocks or ()):
                    continue
                _oc_plast = _oc_pp.get_last_instruction()
                if _oc_plast is None or _oc_plast.argval is None:
                    continue
                if _oc_plast.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
                    continue
                if 'FALSE' not in _oc_plast.opname:
                    continue
                if _oc_plast.argval != _oc_tail_off:
                    continue
                if any(_oc_s.start_offset == _oc_head.start_offset
                       for _oc_s in _oc_pp.conditional_successors):
                    _oc_entry_skip = True
                    break
        # [v143-ORCHAIN] or 链前向闭合（只增不破）：or 链（``while A or B:``）
"""

TAIL_OLD = """                                        chain = [(b, 'and') for b in _on_heads] + [
                                            (_oc_b, 'or') for _oc_b, _ in chain]
                                return chain
"""

TAIL_NEW = """                                        chain = [(b, 'and') for b in _on_heads] + [
                                            (_oc_b, 'or') for _oc_b, _ in chain]
                                        _oc_prefixed = True
                                if _oc_entry_skip and not _oc_prefixed:
                                    return None
                                return chain
"""

HUNKS = (('A', HUNK_OLD, HUNK_NEW), ('B', TAIL_OLD, TAIL_NEW))


def read(path):
    raw = open(path, 'rb').read()
    return raw.decode('utf-8-sig'), raw.startswith(b'\xef\xbb\xbf')


def write(path, text, bom):
    with open(path, 'wb') as fh:
        if bom:
            fh.write(b'\xef\xbb\xbf')
        fh.write(text.encode('utf-8'))


def main(argv):
    revert = '--revert' in argv[1:]
    root = DEFAULT_ROOT
    args = argv[1:]
    for i, a in enumerate(args):
        if a == '--root' and i + 1 < len(args):
            root = args[i + 1]
        elif a.startswith('--root='):
            root = a.split('=', 1)[1]
    path = os.path.join(root, TARGET)
    text, bom = read(path)
    print('target: %s bom=%s' % (path, bom))
    changed = 0
    for name, old, new in HUNKS:
        src, dst = (new, old) if revert else (old, new)
        n = text.count(src)
        print('hunk %s anchor count=%d -> %s' % (name, n, 'REVERT' if revert else 'APPLY'))
        if n == 0:
            if text.count(dst) == 1:
                print('  already in target state, skip')
                continue
            print('  ERROR: anchor not found and target state not present')
            return 2
        if n != 1:
            print('  ERROR: anchor not unique')
            return 2
        text = text.replace(src, dst)
        changed += 1
    if changed:
        write(path, text, bom)
        print('wrote %d hunk(s), bytes=%d' % (changed, len(text.encode('utf-8'))))
        if bom and open(path, 'rb').read(3) != b'\xef\xbb\xbf':
            print('  ERROR: BOM lost')
            return 4
    else:
        print('nothing to do')
    tmp = tempfile.mkdtemp()
    try:
        py_compile.compile(path, cfile=os.path.join(tmp, 'p.pyc'), doraise=True)
        print('py_compile: OK')
    except py_compile.PyCompileError as exc:
        print('py_compile: FAILED %s' % exc)
        return 3
    print('sha256(file)=%s' % hashlib.sha256(open(path, 'rb').read()).hexdigest())
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
