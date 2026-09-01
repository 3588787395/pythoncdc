# repro_11: Pattern B — LOAD_FAST -> LOAD_GLOBAL (local resolved as global)
# Pattern: B-SCOPE resolution (closure/local var emitted as global)
# Original failing function: get_multiminute_his_data_by_date (klinedata.pyc, true_diffs=492)
# Ported from R03 repro_13 (true_diffs=13, jump_diffs=5)
# Expected: local _1m_df_nan_data -> LOAD_FAST
# Actual (pre-fix): orig index 48 LOAD_FAST '_1m_df_nan_data' vs decomp LOAD_GLOBAL 'get_kline_time_by_asset'
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
# --- verification result ---
# verdict: DEFECT-REPRO
# mismatch_fn: f
# true_diffs: 13, jump_diffs: 5
# first_diff: index=20 orig=LOAD_METHOD 'append' vs decomp=LOAD_FAST 'out'
