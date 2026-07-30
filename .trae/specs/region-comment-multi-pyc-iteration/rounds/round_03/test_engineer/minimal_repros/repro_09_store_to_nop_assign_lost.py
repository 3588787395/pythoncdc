# repro_09: STORE_FAST -> NOP (assignment lost in try/except + if/elif + ternary)
# Pattern: ASSIGNMENT-LOST (STORE_FAST replaced by NOP; ternary result never bound in try body)
# Original failing function: klineCacheData_to_dict (klinedata.pyc, true_diffs=166)
# Expected: try: symbol = row.get('symbol') -> STORE_FAST symbol
# Actual diff summary: orig index 30 STORE_FAST 'symbol' vs decomp NOP
# Expected vs actual bytecode diff: index 30 orig_op=STORE_FAST decomp_op=NOP
EMPTY = {}


def f(row, default):
    try:
        symbol = row.get('symbol')
        date = row.get('date')
        out = {}
        if symbol is None:
            out['symbol'] = default
        elif symbol == '':
            out['symbol'] = default
        else:
            out['symbol'] = symbol if symbol != 'x' else default
        if date is not None:
            out['date'] = date
        return out
    except BaseException:
        return EMPTY
# --- verification result ---
# verdict: NO-DEFECT
# mismatch_fn: None
# true_diffs: 0, jump_diffs: 0
# 
