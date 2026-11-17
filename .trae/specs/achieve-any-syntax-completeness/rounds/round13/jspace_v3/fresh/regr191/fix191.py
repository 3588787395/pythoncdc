# -*- coding: utf-8 -*-
"""rr-v5r191 patch: narrow the r172 [v172-NEGAND] polarity normaliser.

Single method, `core/cfg/region_analyzer.py::_v172_negated_and_operand_op_types`
(wired in once, at `_create_boolop_region_from_chain`).

r172 wanted to give a negated conjunct its `and` label back.  In a *condition*
context CPython 3.11 compiles `not X` without `UNARY_NOT`: it emits a
TRUE-polarity conditional jump whose target is the failure exit of the and
chain, so the operand-pair `(X, jump)` looks exactly like a plain `or` member.
The hunk relabels such members from 'or' to 'and'; the build layer then restores
the implicit `not` from the TRUE jump direction.

The premise "a last-member FALSE-polarity jump whose target is `exit_off` makes
that exit the *failure* exit of an and chain" only holds for the **popping**
conditional-jump family (`POP_JUMP_*`, CONDITIONAL_JUMP_OPS): those pop the
tested value before jumping, so their target can only be a control-flow exit.

`JUMP_IF_TRUE_OR_POP` / `JUMP_IF_FALSE_OR_POP` (SHORT_CIRCUIT_JUMP_OPS) are
*value-keeping* short circuits: when taken they leave the operand on the stack
as the expression result, so their target is always the value merge.  In a value
context the two jumps of `a or (b and c)` therefore land on the *same* block
(the merge), which the old test reads as "TRUE jump to the and-chain exit" and
relabels the `or` member as `and`; the build layer then adds the implicit `not`
=> `return not a and b and c` instead of `return a or (b and c)`
(test_repros/round3/e02_g1_b98_hosts.pyc: `f_match_arm_host`,
`CB98.m_class_body_host`).  In a value context the compiler spells negation as an
explicit `UNARY_NOT` inside the operand block, so the normaliser has nothing to
restore there.

Narrowing = add one structural conjunct: the candidate member must end in
CONDITIONAL_JUMP_OPS (a popping conditional jump).  The accepted set is a strict
subset of r172's; anything not matched keeps its label bit-for-bit (C3), and the
criterion reads only the member's own last instruction opcode/argval ([C1]
same-level structural fact) - no names, offsets, counters or thresholds.

Usage:
    python fix191.py            # apply (idempotent, skips an already-applied hunk)
    python fix191.py --revert   # revert to the pre-patch bytes
    python fix191.py --root DIR # patch the tree at DIR (default: the repo)
"""
import hashlib
import os
import py_compile
import sys
import tempfile

DEFAULT_ROOT = r'F:\Downloads\pythoncdc-main'
TARGET = os.path.join('core', 'cfg', 'region_analyzer.py')

HUNK_OLD = """        fixed = []
        changed = False
        for block, op in chain:
            if op == 'or':
                _li = block.get_last_instruction()
                if (_li is not None and 'TRUE' in _li.opname
                        and getattr(_li, 'argval', None) == exit_off):
                    op = 'and'
                    changed = True
            fixed.append((block, op))
"""

HUNK_NEW = """        fixed = []
        changed = False
        for block, op in chain:
            if op == 'or':
                _li = block.get_last_instruction()
                # [v191-POPPOL] 候选必须是**弹栈型条件跳转**（CONDITIONAL_JUMP_OPS）。
                # 依据：POP_JUMP_* 先弹掉被测值再跳，其目标只能是控制流出口，故
                # 「TRUE 极性且目标 == and 链出口」才等价于「本项为真 ⇒ 整链失败」
                # = 隐式 not。JUMP_IF_TRUE_OR_POP 属**保值型**短路跳转
                # （SHORT_CIRCUIT_JUMP_OPS）：跳转时把该操作数留在栈上作为表达式
                # 结果送往 merge，目标恒为值汇合块，永远不是失败出口。值语境
                # `a or (b and c)` 的链恰为 [(or, JUMP_IF_TRUE_OR_POP→merge),
                # (and, JUMP_IF_FALSE_OR_POP→merge)]：两条短路目标重合于 merge，
                # 旧判据据此把 or 成员改标 'and'，构建层再按 TRUE 极性补隐式 not
                # ⇒ `not a and b and c`（极性反转）。值语境的取反由编译器以
                # UNARY_NOT 显式给出，本归一化无事可做 —— 故把接受集收窄到弹栈
                # 族，判据只读成员末指令 opcode/argval（[C1] 同层结构事实），
                # 不命中即逐位保持（C3）。
                if (_li is not None and 'TRUE' in _li.opname
                        and _li.opname in CONDITIONAL_JUMP_OPS
                        and getattr(_li, 'argval', None) == exit_off):
                    op = 'and'
                    changed = True
            fixed.append((block, op))
"""

DOC_OLD = """        C 条款：[C1] 只读链成员末指令 opname/argval 与后继集合；[C2] 判据只
        命中「TRUE 极性且目标 = and 链出口」的成员，其余逐位保持（无 'or'
        成员命中时原链原样返回）；[C3] 不命中即返回原对象，无语义/发射差。
"""

DOC_NEW = """        C 条款：[C1] 只读链成员末指令 opname/argval 与后继集合；[C2] 判据只
        命中「弹栈型条件跳转（CONDITIONAL_JUMP_OPS）且 TRUE 极性且目标 = and
        链出口」的成员，其余逐位保持（无 'or' 成员命中时原链原样返回）；[C3]
        不命中即返回原对象，无语义/发射差。
"""

HUNKS = (('A', HUNK_OLD, HUNK_NEW), ('B', DOC_OLD, DOC_NEW))


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
