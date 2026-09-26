# -*- coding: utf-8 -*-
"""最小复现：CPython 3.11 里推导式过滤条件的跳转方向随 and 链操作数的源码行界而变。

  python -X utf8 synth/linebreak_and_jump.py

同一段 `if A and B`：
  * A、B 同处一行      -> A 的条件跳转是 POP_JUMP_BACKWARD_IF_FALSE -> 循环头(偏移 8)
  * A、B 之间换行      -> A 的条件跳转是 POP_JUMP_FORWARD_IF_FALSE  -> 循环体末尾(偏移 114)
两条跳转的 argval（目标偏移）不同，重编译产物与原 pyc 的字节码因此分叉，
这正是 future_position / live_future_position / option_position 十个
`<genexpr>` 单元 "Different bytecode" 的全部原因。
`if A if B`（两个独立过滤条件）在同一行上同样是回跳形态，换行后同样前跳——
所以单行产物无论怎么改 AST 形状都复现不了原字节码，唯一自由度是源码行界。
"""
import dis
import sys

sys.stdout.reconfigure(encoding='utf-8')

ONE_LINE = (
    "def f(orders, BUY, OPEN):\n"
    "    return sum((o.unfilled for o in orders if o.dir == BUY and o.dir2 == OPEN))\n"
)
SPLIT = (
    "def f(orders, BUY, OPEN):\n"
    "    return sum((o.unfilled for o in orders if o.dir == BUY\n"
    "                and o.dir2 == OPEN))\n"
)
TWO_IF_SAME_LINE = (
    "def f(orders, BUY, OPEN):\n"
    "    return sum((o.unfilled for o in orders if o.dir == BUY if o.dir2 == OPEN))\n"
)


def genexpr_ops(src):
    for c in compile(src, '<synth>', 'exec').co_consts:
        if hasattr(c, 'co_name') and c.co_name == 'f':
            for g in c.co_consts:
                if getattr(g, 'co_name', '') == '<genexpr>':
                    return [(i.opname, i.offset, i.argval)
                            for i in dis.get_instructions(g)]
    raise SystemExit('genexpr not found')


for label, src in (('same line  ', ONE_LINE),
                   ('break a|b  ', SPLIT),
                   ('if A if B  ', TWO_IF_SAME_LINE)):
    ops = genexpr_ops(src)
    cond = [o for o in ops if 'POP_JUMP' in o[0]]
    print('%s  conditional jumps: %s' % (label, cond))

a = [o for o in genexpr_ops(ONE_LINE) if 'POP_JUMP' in o[0]]
b = [o for o in genexpr_ops(SPLIT) if 'POP_JUMP' in o[0]]
assert a[0][0] != b[0][0] and a[0][2] != b[0][2], 'expected direction flip'
print('\n首条条件跳转：同行=%s -> %d，换行=%s -> %d  （argval 即目标偏移，字节码因此分叉）'
      % (a[0][0], a[0][2], b[0][0], b[0][2]))
