"""Compile the hypothesised source for the compound while and dump it with resolved jump targets,
to check whether CPython 3.11 reproduces the original's entry-chain + re-test-chain shape.
"""
import dis
import sys

SRC = '''
import time
from datetime import datetime


def f(pre_before_trading, post_after_trading, holiday_sync_account, self):
    while (int(datetime.now().strftime('%H%M')) < pre_before_trading
           or int(datetime.now().strftime('%H%M')) >= int(post_after_trading)
           or holiday_sync_account == '0'
           and not self.engine.data_proxy.is_trading_date(datetime.now().date())):
        time.sleep(60)
    x = 1
'''

comp = compile(SRC, '<p>', 'exec')


def walk(c):
    yield c
    for k in c.co_consts:
        if isinstance(k, type(c)):
            yield from walk(k)


co = [c for c in walk(comp) if c.co_name == 'f'][0]
kept = [i for i in dis.get_instructions(co) if i.opname not in ('NOP', 'CACHE', 'EXTENDED_ARG')]
off2idx = {i.offset: k for k, i in enumerate(kept)}
for k, i in enumerate(kept):
    tg = list(getattr(i, 'targets', None) or [])
    t = '  -> ' + ','.join('@%d#%d' % (g, off2idx.get(g, -1)) for g in tg) if tg else ''
    print('[%-4d] @%-6d %-28s %s%s' % (k, i.offset, i.opname, i.argrepr or '', t))
