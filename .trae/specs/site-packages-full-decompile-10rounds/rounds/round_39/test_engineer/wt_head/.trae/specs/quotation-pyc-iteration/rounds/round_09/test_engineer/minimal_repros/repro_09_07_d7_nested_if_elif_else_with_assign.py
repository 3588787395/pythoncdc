"""Repro 09-07: D7 variant — nested if/elif/else with assignments (4 outer branches).

The quotation.pyc::build_future_fill_time defect has a nested structure
with 4 outer branches (typet == 2/3/4/13). R8 repro_08_03 confirmed
D7 fires with 4 outer branches. This repro is the R9 minimal form
with 4 outer branches × 2 inner branches.

The decompiler collapses the outer if/elif over `typet` into a nested
ternary, mis-attributing the inner `if suffix == 'T.CCFX'` condition
as the ternary body, and converting `=` assignments to `==`
comparisons.

Expected defect: a single bare Expr of nested ternary of `==`.
"""


def build_market(typet, suffix):
    if typet == 2:
        if suffix == 'T.CCFX':
            market_time = {'open': '09:35'}
        else:
            market_time = {'open': '09:00'}
    elif typet == 3:
        if suffix == 'T.CCFX':
            market_time = {'open': '09:30'}
        else:
            market_time = {'open': '09:00'}
    elif typet == 4:
        if suffix == 'T.CCFX':
            market_time = {'open': '09:25'}
        else:
            market_time = {'open': '09:00'}
    elif typet == 13:
        market_time = {'open': '09:00'}
    return market_time
