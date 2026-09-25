# diag4 targets (3 files, official gap 7, strict defects 8)

## IQData/plugins/plugin_system_realquote/real_quote.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQData/plugins/plugin_system_realquote/real_quote.pyc
   official 40/44 (gap 4)   strict 41/45 (defects 4, missing 0, extra 0)
   OFF    get_cache_l2_data_by_one                     orig=321   decomp=322   hunks=2  first_diff=197
   OFF    get_real_minute_kline                        orig=253   decomp=254   hunks=3  first_diff=197
   OFF    get_tick_direction                           orig=259   decomp=258   hunks=3  first_diff=102
   OFF    one_prod_to_ndarray                          orig=605   decomp=607   hunks=5  first_diff=424
   STRICT get_cache_l2_data_by_one                     [seq_len] orig=321 decomp=322
   STRICT get_real_minute_kline                        [seq_len] orig=253 decomp=256
   STRICT get_tick_direction                           [seq_len] orig=259 decomp=260
   STRICT one_prod_to_ndarray                          [seq_len] orig=606 decomp=608

## IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc
   official 32/34 (gap 2)   strict 33/36 (defects 3, missing 0, extra 0)
   OFF    future_order                                 orig=101   decomp=92    hunks=2  first_diff=36
   OFF    option_order                                 orig=83    decomp=73    hunks=3  first_diff=39
   STRICT base_order                                   [target_diff] #136 POP_JUMP_IF_TRUE 终点 orig=("'order_obj'", 'LOAD_FAST') decomp=("'生成订单，订单号:{order_id}，可转债代码：{symbol}，数量：{side}{share}'", 'LOAD_CONST')
   STRICT future_order                                 [seq_len] orig=101 decomp=93
   STRICT option_order                                 [seq_len] orig=83 decomp=74

## IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc
   official 11/12 (gap 1)   strict 11/12 (defects 1, missing 0, extra 0)
   OFF    clock_worker                                 orig=1275  decomp=1286  hunks=10 first_diff=481
   STRICT clock_worker                                 [seq_len] orig=1276 decomp=1287
