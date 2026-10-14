"""Dump the finally/continue neighbourhood of trade_live_broker._process_cancel_order.

Original @1740..@2060 vs the r38w product (a8155727b47e3bea) at the same window, with the
jump operands resolved to offsets so the per-exit-edge duplication is readable.

usage: python -X utf8 dump_finally_r38.py
"""
import dis
import marshal
import re
import sys

PYC = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc"
PROD = r"D:/Temp/t30/out/r38w_IQEngine_plugins_plugin_system_trade_trade_live_broker.py"
CO = type(compile('', '', 'exec'))
DROP = ('NOP', 'CACHE', 'EXTENDED_ARG', 'RESUME')


def gather(c, acc):
    acc.append(c)
    for x in c.co_consts:
        if isinstance(x, CO):
            gather(x, acc)


def pick(codes, name):
    return max([c for c in codes if c.co_name == name], key=lambda k: len(k.co_code))


def dump(co, frm, to):
    out = []
    for i in dis.get_instructions(co):
        if i.opname in DROP or i.offset < frm or i.offset > to:
            continue
        arg = i.argrepr or ''
        if 'JUMP' in i.opname or i.opname in ('FOR_ITER', 'SEND'):
            arg = '-> @%s' % i.argval
        pos = getattr(i, 'positions', None)
        ln = ''
        if pos is not None and getattr(pos, 'start_line', None):
            ln = 'L%s' % pos.start_line
        out.append('@%-6d %-4s %-28s %s' % (i.offset, ln, i.opname, arg))
    return out


orig = marshal.loads(open(PYC, 'rb').read()[16:])
o, p = [], []
gather(orig, o)
comp = compile(open(PROD, encoding='utf-8-sig').read(), '<p>', 'exec')
gather(comp, p)
oc, pc = pick(o, '_process_cancel_order'), pick(p, '_process_cancel_order')
print('=== ORIGINAL _process_cancel_order @1740..@2060')
print('\n'.join(dump(oc, 1740, 2060)))
print('=== PRODUCT (a8155727b47e3bea) @1700..@2030')
print('\n'.join(dump(pc, 1700, 2030)))
print('=== product source lines 520-575')
L = open(PROD, encoding='utf-8-sig').read().split('\n')
i0 = [i for i, s in enumerate(L) if 'def _process_cancel_order' in s][0]
for n in range(i0, i0 + 55):
    print(n + 1, L[n][:150])
