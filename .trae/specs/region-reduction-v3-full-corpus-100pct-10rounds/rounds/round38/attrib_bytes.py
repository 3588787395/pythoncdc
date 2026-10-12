"""Per-unit `co_code` byte attribution against the original code object for broker's five units.

usage: python -X utf8 attrib_bytes.py <product.py> [<product.py> ...]
Prints bytes_diff / len_delta per unit, with jump operands included - no filters, no window merging,
so a candidate cannot hide a jump-target difference behind an opcode-stream parity reading.
"""
import marshal
import os
import sys

PYC = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc"
UNITS = ('ipo_stocks_order', '_process_cancel_order', '_process_order', '_sync_worker', '_trade_status_handle')
CO = type(compile('', '', 'exec'))


def gather(c, acc):
    acc.append(c)
    for x in c.co_consts:
        if isinstance(x, CO):
            gather(x, acc)


def pick(cs, n):
    return max([c for c in cs if c.co_name == n], key=lambda k: len(k.co_code))


acc = []
gather(marshal.loads(open(PYC, 'rb').read()[16:]), acc)
for prod in sys.argv[1:]:
    comp = compile(open(prod, encoding='utf-8-sig').read(), '<p>', 'exec')
    q = []
    gather(comp, q)
    print('=== %s' % os.path.basename(prod))
    for u in UNITS:
        try:
            o, p = pick(acc, u), pick(q, u)
        except ValueError:
            print('   %-22s unit missing' % u)
            continue
        d = [n for n in range(min(len(o.co_code), len(p.co_code))) if o.co_code[n] != p.co_code[n]]
        print('   %-22s bytes_diff=%4d len_delta=%+d first=%s' % (
            u, len(d), len(o.co_code) - len(p.co_code), d[:4]))
