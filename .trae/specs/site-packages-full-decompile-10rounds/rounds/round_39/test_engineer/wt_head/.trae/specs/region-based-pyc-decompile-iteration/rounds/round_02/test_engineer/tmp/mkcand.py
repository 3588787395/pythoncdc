#!/usr/bin/env python3
"""生成候选最小复现源码到 tmp/cand/。"""
from pathlib import Path

CAND = Path(__file__).resolve().parent / 'cand'
CAND.mkdir(exist_ok=True)
for p in CAND.glob('*.py'):
    p.unlink()

C = {}

C['c01'] = '''def f():
    return object()


f().x = 5
'''

C['c02'] = '''class DataProxy:
    TickBar = TickBar
    BarData = BarData

    def __init__(self):
        self.a = 1
'''

C['c03'] = '''class A:
    def __init__(self, processed_trade=None):
        self._a = 1
        self._processed_trade = processed_trade if processed_trade is not None else set()
        self._b = 2
'''

C['c04'] = '''import numpy as np


def last_price(self):
    if not np.isnan(self._last_price):
        return self._last_price
    return 0
'''

C['c05'] = '''def f(trading_dt, env, trade):
    trade._trading_dt = trading_dt
    trade._calendar_dt = calendar_dt if calendar_dt else env.calendar_dt
'''

C['c06'] = '''def fill(self, trade):
    amount = trade.amount
    assert self.filled_amount + amount <= self.amount
    self.filled_amount += amount
    return [trade]
'''

C['c07'] = '''import six


class B(object):
    def __init__(self, d=None):
        self.__dict__ = dict(list(six.iteritems(self.__dict__)))
        self.x = 1
'''

C['c08'] = '''def __missing__(self, symbol):
    r = self.get(symbol, None)
    if r is not None:
        return r
    symbol = symbol.replace('XSHG', 'SS').replace('XSHE', 'SZ')
    r = self.get(symbol, None)
    if r is not None:
        return r
    try:
        return Position(self._engine.portfolio.positions[symbol])
    except (AttributeError, KeyError):
        return None
'''

C['c09'] = '''def f(d):
    d = d if d is not None else {}
    return d
'''

C['c10'] = '''def f(a, b, cond):
    x = a.m() if cond else b.n()
    return x
'''

C['c11'] = '''def f(items):
    for i in items:
        if i > 0:
            break
    else:
        return None
    return i
'''

C['c12'] = '''def outer():
    def inner(a=1, b=(2, 3)):
        return a + b

    return inner
'''

C['c13'] = '''def f(p):
    with open(p, 'w') as fh:
        fh.write('x')
    return 1
'''

C['c14'] = '''def f(x, y):
    return x if x else y
'''

C['c15'] = '''def f(a, b, c):
    obj.attr = a if a else b.c
    obj2.attr2 = a if a is not None else b.c
'''

C['c16'] = '''def f(x):
    if x is not None:
        return x
    return 0
'''

C['c17'] = '''def f():
    while True:
        x = g()
        if x:
            break
    return x
'''

C['c18'] = '''def f(s):
    return s.replace('XSHG', 'SS').replace('XSHE', 'SZ')
'''

C['c19'] = '''def f(d, k, v):
    d[k] = v
    return d
'''

C['c20'] = '''def f(self, trade):
    self._buy_transaction_cost += trade.transaction_cost
    self._x *= 2
    return self
'''

C['c21'] = '''def f(x):
    if x in ('11', '12'):
        return None
    if y is not None:
        return None
    return 1
'''

C['c22'] = '''def f(a, b):
    if a is None and b is None:
        return 0
    return 1
'''

C['c23'] = '''def f(x):
    y = x if x is not None else 'default'
    z = y
    return z
'''

C['c24'] = '''class C:
    def __init__(self):
        self.a = 0

    def f(self):
        self.a = self.a + 1
        return self.a
'''

C['c25'] = '''def f(self, symbol):
    return self.get(symbol, None)
'''

C['c26'] = '''def f(a, b, c=1, *args, **kw):
    return a(b, *args, **kw)
'''

C['c27'] = '''def f(x):
    try:
        return int(x)
    except ValueError:
        return None
'''

C['c28'] = '''def f(self):
    self._a = 1
    self._b = 2
    return self
'''

C['c29'] = '''def f(x):
    return [i for i in x if i]
'''

C['c30'] = '''def f(x):
    return {k: v for k, v in x.items()}
'''

for name, src in C.items():
    (CAND / f'{name}.py').write_text(src, encoding='utf-8')
print(f'wrote {len(C)} candidates to {CAND}')
