# repro_13: LOAD_FAST -> LOAD_GLOBAL (local resolved as global)
# Pattern: LOCAL->GLOBAL scope resolution (closure/local var emitted as global)
# Original failing function: get_multiminute_his_data_by_date (klinedata.pyc, true_diffs=492)
# Expected: local _1m_df_nan_data -> LOAD_FAST
# Actual diff summary: orig index 48 LOAD_FAST '_1m_df_nan_data' vs decomp LOAD_GLOBAL 'get_kline_time_by_asset'
# Expected vs actual bytecode diff: index 48 orig_op=LOAD_FAST decomp_op=LOAD_GLOBAL
def f(symbol, frequency, start_date, end_date):
    _1m_df_nan_data = {}
    out = []
    for cur in (start_date, end_date):
        if frequency == '1m':
            _1m_df_nan_data[cur] = symbol
            out.append(_1m_df_nan_data)
        else:
            out.append(cur)
    return out
