#!/usr/bin/env python3
"""候选最小复现第二批。"""
from pathlib import Path

CAND = Path(__file__).resolve().parent / 'cand'
CAND.mkdir(exist_ok=True)
for p in CAND.glob('*.py'):
    p.unlink()

C = {}

# F1: 调用结果作为 STORE_ATTR 对象，值被丢成 None
C['d01'] = '''def f():
    return object()


f().x = 5
'''

# F1b: 下标形式
C['d02'] = '''def f():
    return {}


f()['k'] = 5
'''

# F2: 类体内同名别名
C['d03'] = '''class DataProxy:
    TickBar = TickBar
    BarData = BarData

    def __init__(self):
        self.a = 1
'''

# F2b: 类体内别名（不同名）
C['d04'] = '''class C:
    Alias = Other
'''

# F3: 连续两个 `obj.attr = a or b.c`
C['d05'] = '''def create_trade(cls, calendar_dt, trading_dt, env, trade):
    trade._calendar_dt = calendar_dt or env.calendar_dt
    trade._trading_dt = trading_dt or env.trading_dt
    trade._price = price
    return trade
'''

# F3b: 单个
C['d06'] = '''def f(trade, calendar_dt, env):
    trade._calendar_dt = calendar_dt or env.calendar_dt
    return trade
'''

# F4: assert 前的局部赋值
C['d07'] = '''def fill(self, trade):
    amount = trade.amount
    assert self.filled_amount + amount <= self.amount
    self.filled_amount += amount
    return [trade]
'''

# F4b: 无 assert 的对照
C['d08'] = '''def fill(self, trade):
    amount = trade.amount
    if self.filled_amount + amount <= self.amount:
        self.filled_amount += amount
    return [trade]
'''

# F4c: 带消息的 assert
C['d09'] = '''def fill(self, trade):
    amount = trade.amount
    assert self.filled_amount + amount <= self.amount, 'over fill'
    return [trade]
'''

# F5: try/except 之后的 from ... import ... as ...
C['d10'] = '''try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
from _line_profiler import LineProfiler as CLineProfiler
PY3 = sys.version_info[0] == 3
'''

# F5b: 不带 try/except 的对照
C['d11'] = '''from _line_profiler import LineProfiler as CLineProfiler
PY3 = sys.version_info[0] == 3
'''

# F5c: try/except 之后的普通 import
C['d12'] = '''try:
    import a
except ImportError:
    a = None
import b
'''

# F7: with 之后的裸 return
C['d13'] = '''import os


def load(self, file_path):
    if not os.path.exists(file_path):
        return
    with open(file_path, 'r') as fh:
        self.future_info = fh.read()
    return
'''

# F7b: with 之后还有代码
C['d14'] = '''import os


def load(self, file_path):
    with open(file_path, 'r') as fh:
        self.future_info = fh.read()
    return
'''

# F7c: if 里的裸 return，后面还有语句
C['d15'] = '''def f(x):
    if x:
        return
    g(x)
    h(x)
'''

# F8: 多目标下标赋值
C['d16'] = '''def func_wrapper(start, end, call_args, range_start_args, cache_start, on_off_limit_start):
    start_ = call_args[range_start_args] = on_off_limit_start(start)
    call_args[end] = cache_start
    return start_
'''

# F8b: 纯下标赋值
C['d17'] = '''def f(call_args, end, cache_start):
    call_args[end] = cache_start
    return call_args
'''

# F9: for + continue 形状
C['d18'] = '''def getchnstr(input_str, MAP, SCORE, DECIMAL):
    chn_str = ''
    for c in input_str:
        if c in MAP.keys() or c in SCORE:
            continue
        if c in DECIMAL:
            chn_str = chn_str + c
        if len(chn_str) > 0:
            break
    return chn_str
'''

# F9b: for/else
C['d19'] = '''def f(items):
    for i in items:
        if i > 0:
            break
    else:
        return None
    return i
'''

# F10: 三元 + STORE_ATTR
C['d20'] = '''class A:
    def __init__(self, total_cash, positions, processed_trade=None):
        self._total_cash = total_cash
        self._processed_trade = processed_trade if processed_trade is not None else set()
        self._transaction_cost = 0
        self.register_event()
'''

# F10b: 只有三元
C['d21'] = '''class A:
    def __init__(self, processed_trade=None):
        self._processed_trade = processed_trade if processed_trade is not None else set()
'''

# F10c: 三元 + 后续调用
C['d22'] = '''class A:
    def __init__(self, processed_trade=None):
        self._a = 1
        self._processed_trade = processed_trade if processed_trade is not None else set()
        self._b = 0
        self.register_event()
'''

# F11: if not f(x) + raise
C['d23'] = '''def last_price(self, np, Engine):
    if not np.isnan(self._last_price):
        return self._last_price
    last_price = Engine.instance().get_last_price(self.symbol)
    if np.isnan(last_price):
        raise RuntimeError('nan'.format(self.symbol))
    return last_price
'''

# F12: try/except (AttributeError, KeyError) 在 if 之后
C['d24'] = '''def __missing__(self, symbol, Position):
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

# F13: 单指令差异 — 常量变 None（下标 + 调用）
C['d25'] = '''def f():
    return {}


g()['k'] = f()
'''

# F14: if not in 循环
C['d26'] = '''def f(items, bad):
    out = []
    for i in items:
        if i not in bad:
            out.append(i)
    return out
'''

for name, src in C.items():
    (CAND / f'{name}.py').write_text(src, encoding='utf-8')
print(f'wrote {len(C)} candidates')
