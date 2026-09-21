# -*- coding: utf-8 -*-
# R24 battery case a01_cc_ternary_nested_guard
# SHAPE: a chained-compare conditional expression assigned to a name, sitting one level
#        inside a truthiness guard (mirrors IQData/plugin_system_realquote/real_quote
#        .get_real_L2_data and its near-twin fly/data/quote.get_individual_data), plus a
#        second site where the same ternary follows an early-return guard.
# EXPECTED: the site is emitted as ONE ternary assignment statement.
# ACTUAL-HEAD: FAIL -- the assignment is dropped entirely; only the bare arm expressions
#              survive (`if 0 < int(data_count) <= 200: int(data_count) else: 200`), so
#              `data_count` is never rebound.  official 1/3.
# ACTUAL-CAND: OK   -- `data_count = int(data_count) if ... else 200` restored.  official 3/3.
# MARK: PRED_R24A_FIX
# MUST_CONTAIN: data_count = int(data_count) if 0 < int(data_count) <= 200 else 200
def get_real_like(symbols, data_count):
    if symbols:
        data_count = int(data_count) if 0 < int(data_count) <= 200 else 200
        if isinstance(symbols, str):
            symbols = [symbols]
        else:
            symbols = list(symbols)
    return data_count, symbols


def get_by_one_like(data_count, symbols, flags):
    if symbols:
        return flags
    data_count = int(data_count) if 0 < int(data_count) <= 200 else 200
    for s in symbols:
        if isinstance(s, str):
            symbols = [s]
    return data_count, symbols
