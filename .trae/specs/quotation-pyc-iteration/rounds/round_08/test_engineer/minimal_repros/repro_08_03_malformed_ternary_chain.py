"""Repro 08-03: D7 (P2) malformed ternary chain (if/elif compressed).

In `build_future_fill_time` (quotation.pyc line 351) the source is:
    if typet == 2:
        if suffix == 'T.CCFX':
            market_time = {...}
        elif suffix in ('XZCE', ...):
            ...
        else:
            ...
    elif typet == 3:
        ...
    elif typet == 4:
        ...
    elif typet == 13:
        ...
The decompiler collapses this into a single nested ternary:
    suffix == 'T.CCFX' if typet == 2 else suffix == 'T.CCFX' if typet == 3 else
    suffix == 'T.CCFX' if typet == 4 else typet == 13
The `=` assignments become `==` comparisons, and the if/elif becomes
a bare Expr.

Expected defect: a single bare Expr of nested ternary of `==`.
"""


def build_market(typet, suffix):
    if typet == 2:
        if suffix == 'T.CCFX':
            market_time = {'open_am': '09:35:00'}
        elif suffix in ('XZCE', 'XDCE', 'XSGE'):
            market_time = {'open_am': '09:05:00'}
        else:
            market_time = {'open_am': '09:35:00'}
    elif typet == 3:
        if suffix == 'T.CCFX':
            market_time = {'open_am': '09:30:00'}
        else:
            market_time = {'open_am': '09:00:00'}
    elif typet == 4:
        if suffix == 'T.CCFX':
            market_time = {'open_am': '09:25:00'}
        else:
            market_time = {'open_am': '09:00:00'}
    elif typet == 13:
        market_time = {'open_am': '09:00:00'}
    return market_time
