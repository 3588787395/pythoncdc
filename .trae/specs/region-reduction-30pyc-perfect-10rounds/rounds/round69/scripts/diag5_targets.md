# diag5 targets (2 files, official gap 3, strict defects 7)

## IQCommon/util/trade_info_utils.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQCommon/util/trade_info_utils.pyc
   official 39/40 (gap 1)   strict 37/41 (defects 4, missing 0, extra 0)
   OFF    trade_operation                              orig=304   decomp=302   hunks=2  first_diff=40
   STRICT get_trade_status                             [target_diff] #70 FOR_ITER 终点 orig=("'return_trade_info'", 'LOAD_FAST') decomp=("'count'", 'LOAD_FAST')
   STRICT get_trade_unit_info                          [seq_len] orig=240 decomp=241
   STRICT set_trade_status                             [target_diff] #113 JUMP 终点 orig=("'count'", 'LOAD_FAST') decomp=("'exchange_flag'", 'LOAD_FAST')
   STRICT trade_operation                              [seq_len] orig=304 decomp=302

## IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc
   official 33/35 (gap 2)   strict 34/37 (defects 3, missing 0, extra 0)
   OFF    _on_publish_after_trading_end                orig=486   decomp=481   hunks=3  first_diff=33
   OFF    _save_testds_to_csv                          orig=71    decomp=68    hunks=7  first_diff=19
   STRICT _on_publish_after_trading_end                [seq_len] orig=488 decomp=481
   STRICT _on_set_positions                            [seq_len] orig=297 decomp=298
   STRICT _save_testds_to_csv                          [seq_len] orig=75 decomp=68
