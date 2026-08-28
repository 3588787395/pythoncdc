#!/usr/bin/env python3
"""候选最小复现第三批：try/except 范围、import 位置、return None 插入。"""
from pathlib import Path

CAND = Path(__file__).resolve().parent / 'cand3'
CAND.mkdir(exist_ok=True)

C = {}

# try 范围被扩大
C['e01'] = '''def __missing__(self, symbol):
    symbol = endswith_transe_2to4(symbol)
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
        raise KeyError(symbol)
'''

C['e02'] = '''def f(self, symbol):
    try:
        return Position(self._engine.portfolio.positions[symbol])
    except (AttributeError, KeyError):
        raise KeyError(symbol)
'''

C['e03'] = '''def f(self, k):
    r = self.get(k, None)
    if r is not None:
        return r
    try:
        return Position(self.a.b[k])
    except (AttributeError, KeyError):
        raise KeyError(k)
'''

# import 在 if 块内
C['e04'] = '''def setup(self, engine):
    if engine.config.other.enable_debug:
        import ptvsd
        if get_python_version() == '3.11':
            ptvsd.reset()
        engine.config.other.enable_debug = config.timeout or 10
'''

C['e05'] = '''def setup(self, engine):
    import ptvsd
    engine.config.other.enable_debug = config.timeout or 10
'''

C['e06'] = '''def f(engine):
    if engine.debug:
        import ptvsd
        engine.x = ptvsd.y() or 10
        engine.z = 1
'''

# 三元/局部
C['e07'] = '''def f(a):
    b = a if a is not None else g()
    return b
'''

C['e08'] = '''class A:
    def __init__(self, p=None):
        self.x = 1
        self.y = p if p is not None else []
        self.z = 0
'''

# for/else 变体
C['e09'] = '''def f(items):
    for i in items:
        if i > 0:
            break
    else:
        return None
    return i
'''

C['e10'] = '''def f(items):
    for i in items:
        if i > 0:
            break
    else:
        i = 0
    return i
'''

C['e11'] = '''def f(n):
    while n > 0:
        n -= 1
    else:
        return -1
    return n
'''

# assert 变体
C['e12'] = '''def f(self, trade):
    amount = trade.amount
    assert self.a + amount <= self.b, 'over'
    return amount
'''

C['e13'] = '''def f(a, b):
    assert a > b
    return a
'''

C['e14'] = '''def f(self, x):
    y = self.compute(x)
    assert y is not None
    self.result = y
'''

# 连续 or 赋值变体
C['e15'] = '''def f(o, a, b, c, env):
    o.x = a or env.a
    o.y = b or env.b
    o.z = c
    return o
'''

C['e16'] = '''def f(o, a, b, env):
    o.x = a or env.a
    o.y = b or env.b
    return o
'''

# 调用结果属性
C['e17'] = '''def f():
    return object()


f().x = 5
'''

C['e18'] = '''def f():
    return object()


d = {}
d['k'] = f().x
'''

C['e19'] = '''def f():
    return object()


f().x += 1
'''

C['e20'] = '''def f(a):
    g(a).x = a.b or a.c
'''

for name, src in C.items():
    (CAND / f'{name}.py').write_text(src, encoding='utf-8')
print(f'wrote {len(C)} candidates')
