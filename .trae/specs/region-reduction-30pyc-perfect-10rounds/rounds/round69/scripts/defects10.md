# Round 69 round-open defect table (10 partials)
source: pyc_index.json (status=partial) + R68-verified dumps; official gap = functions whose
instruction streams differ, strict = the stricter comparator over the SHIPPED products.

## IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc
   official 108/119  gap=11   strict 106/123  defects=17  missing=0 extra=0
   OFF  _process_cancel_order                      orig=294   decomp=293   hunks=16 first_diff=22
   OFF  _process_order                             orig=454   decomp=396   hunks=9  first_diff=349
   OFF  _sync_worker                               orig=349   decomp=347   hunks=0  first_diff=296
   OFF  _trade_status_handle                       orig=114   decomp=112   hunks=0  first_diff=107
   OFF  after_trading_cancel_order                 orig=155   decomp=155   hunks=3  first_diff=122
   OFF  etf_basket_order                           orig=693   decomp=693   hunks=11 first_diff=216
   OFF  etf_purchase_redemption                    orig=377   decomp=369   hunks=1  first_diff=37
   OFF  get_max_amount                             orig=201   decomp=213   hunks=2  first_diff=18
   OFF  ipo_stocks_order                           orig=1075  decomp=1075  hunks=18 first_diff=278
   OFF  on_order_response                          orig=445   decomp=444   hunks=6  first_diff=57
   OFF  on_trade_response                          orig=392   decomp=391   hunks=6  first_diff=57
   STRICT _process_cancel_order                      [seq_len] orig=295 decomp=297
   STRICT _process_order                             [seq_len] orig=454 decomp=399
   STRICT _process_tick_order                        [target_diff] #27 JUMP 终点 orig=("'len'", 'LOAD_GLOBAL') decomp=("'self'", 'LOAD_FAST')
   STRICT _sync_worker                               [seq_len] orig=350 decomp=347
   STRICT _trade_status_handle                       [seq_len] orig=114 decomp=112
   STRICT after_trading_cancel_order                 [seq_len] orig=156 decomp=159
   STRICT etf_basket_order                           [seq_diff] #254 orig=("'strategy_log'", 'LOAD_GLOBAL') decomp=("'entrust_price'", 'LOAD_FAST')
   STRICT etf_purchase_redemption                    [seq_len] orig=379 decomp=369
   STRICT get_ipo_stocks                             [target_diff] #189 POP_JUMP_IF_TRUE 终点 orig=("'str'", 'LOAD_GLOBAL') decomp=(None, 'FOR_ITER')
   STRICT get_max_amount                             [seq_len] orig=201 decomp=213
   STRICT ipo_stocks_order                           [seq_diff] #624 orig=("'new_stock'", 'LOAD_FAST') decomp=('<JUMP>', 'JUMP')
   STRICT on_order_response                          [seq_len] orig=449 decomp=448
   STRICT on_order_response_list_handle              [target_diff] #23 POP_JUMP_IF_NONE 终点 orig=("'entrust_no'", 'LOAD_FAST') decomp=(None, 'FOR_ITER')
   STRICT on_pre_before_trading_start                [target_diff] #4 POP_JUMP_IF_FALSE 终点 orig=("'self'", 'LOAD_FAST') decomp=("'datetime'", 'LOAD_GLOBAL')
   STRICT on_trade_response                          [seq_len] orig=396 decomp=395
   STRICT on_trade_response_list_handle              [target_diff] #23 POP_JUMP_IF_NONE 终点 orig=("'entrust_no'", 'LOAD_FAST') decomp=(None, 'FOR_ITER')
   STRICT rzrq_credit_order                          [target_diff] #406 JUMP 终点 orig=("'Order'", 'LOAD_GLOBAL') decomp=("'EntrustDirection'", 'LOAD_GLOBAL')

## fly/data/quote.pyc
   official 70/81  gap=11   strict 74/89  defects=15  missing=0 extra=0
   OFF  build_current_period_df                    orig=115   decomp=108   hunks=5  first_diff=12
   OFF  check_frequency                            orig=121   decomp=120   hunks=1  first_diff=21
   OFF  check_limit                                orig=330   decomp=311   hunks=2  first_diff=248
   OFF  get_individual_data                        orig=312   decomp=311   hunks=1  first_diff=156
   OFF  get_price                                  orig=230   decomp=232   hunks=0  first_diff=172
   OFF  get_real_from_zeromq                       orig=703   decomp=678   hunks=0  first_diff=660
   OFF  initImagedata                              orig=243   decomp=225   hunks=0  first_diff=190
   OFF  load_bars_from_hundsun                     orig=477   decomp=483   hunks=0  first_diff=410
   OFF  load_get_price                             orig=171   decomp=171   hunks=0  first_diff=1
   OFF  run_individual_transform                   orig=362   decomp=321   hunks=2  first_diff=263
   OFF  run_tick_socket                            orig=306   decomp=307   hunks=2  first_diff=228
   STRICT build_current_period_df                    [seq_len] orig=118 decomp=109
   STRICT change_his_to_backward                     [target_diff] #213 POP_JUMP_IF_TRUE 终点 orig=("'data'", 'LOAD_FAST') decomp=('None', 'POP_TOP')
   STRICT change_his_to_forward                      [target_diff] #241 POP_JUMP_IF_FALSE 终点 orig=("'preindex'", 'LOAD_FAST') decomp=(None, 'FOR_ITER')
   STRICT check_frequency                            [seq_len] orig=123 decomp=124
   STRICT check_industry_code                        [seq_diff] #159 orig=('0', 'CONTAINS_OP') decomp=('1', 'CONTAINS_OP')
   STRICT check_limit                                [seq_len] orig=331 decomp=311
   STRICT get_individual_data                        [seq_len] orig=314 decomp=313
   STRICT get_price                                  [seq_len] orig=230 decomp=232
   STRICT get_real_from_zeromq                       [seq_len] orig=703 decomp=678
   STRICT initImagedata                              [seq_len] orig=245 decomp=225
   STRICT load_bars_from_hundsun                     [seq_len] orig=477 decomp=483
   STRICT load_get_price                             [seq_diff] #53 orig=('<JUMP>', 'POP_JUMP_IF_FALSE') decomp=('None', 'POP_TOP')
   STRICT run_individual_transform                   [seq_len] orig=364 decomp=321
   STRICT run_tick_socket                            [seq_len] orig=309 decomp=310
   STRICT run_tick_transform                         [target_diff] #56 POP_JUMP_IF_FALSE 终点 orig=("'len'", 'LOAD_GLOBAL') decomp=("'self'", 'LOAD_FAST')

## IQData/plugins/plugin_system_realquote/real_quote.pyc
   official 40/44  gap=4   strict 41/45  defects=4  missing=0 extra=0
   OFF  get_cache_l2_data_by_one                   orig=321   decomp=322   hunks=2  first_diff=197
   OFF  get_real_minute_kline                      orig=253   decomp=254   hunks=3  first_diff=197
   OFF  get_tick_direction                         orig=259   decomp=258   hunks=3  first_diff=102
   OFF  one_prod_to_ndarray                        orig=605   decomp=607   hunks=5  first_diff=424
   STRICT get_cache_l2_data_by_one                   [seq_len] orig=321 decomp=322
   STRICT get_real_minute_kline                      [seq_len] orig=253 decomp=256
   STRICT get_tick_direction                         [seq_len] orig=259 decomp=260
   STRICT one_prod_to_ndarray                        [seq_len] orig=606 decomp=608

## IQCommon/api/klinedata.pyc
   official 43/45  gap=2   strict 58/63  defects=5  missing=0 extra=0
   OFF  get_multiminute_his_data                   orig=479   decomp=478   hunks=3  first_diff=16
   OFF  kline_datetime_list                        orig=389   decomp=389   hunks=9  first_diff=228
   STRICT get_history_common                         [target_diff] #41 POP_JUMP_IF_NONE 终点 orig=("'is_dict'", 'LOAD_FAST') decomp=("'fields'", 'LOAD_FAST')
   STRICT get_kline_by_count_new                     [target_diff] #161 POP_JUMP_IF_NONE 终点 orig=('0', 'LOAD_CONST') decomp=("'symbols'", 'LOAD_FAST')
   STRICT get_multiminute_his_data                   [seq_len] orig=481 decomp=482
   STRICT get_price_common                           [target_diff] #114 POP_JUMP_IF_NONE 终点 orig=("'frequency'", 'LOAD_FAST') decomp=("'is_dict'", 'LOAD_FAST')
   STRICT kline_datetime_list                        [seq_diff] #151 orig=('<JUMP>', 'POP_JUMP_IF_TRUE') decomp=('<JUMP>', 'POP_JUMP_IF_FALSE')

## IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc
   official 32/34  gap=2   strict 33/36  defects=3  missing=0 extra=0
   OFF  future_order                               orig=101   decomp=92    hunks=2  first_diff=36
   OFF  option_order                               orig=83    decomp=73    hunks=3  first_diff=39
   STRICT base_order                                 [target_diff] #136 POP_JUMP_IF_TRUE 终点 orig=("'order_obj'", 'LOAD_FAST') decomp=("'生成订单，订单号:{order_id}，可转债代码：{symbol}，数量：{si
   STRICT future_order                               [seq_len] orig=101 decomp=93
   STRICT option_order                               [seq_len] orig=83 decomp=74

## IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc
   official 33/35  gap=2   strict 34/37  defects=3  missing=0 extra=0
   OFF  _on_publish_after_trading_end              orig=486   decomp=481   hunks=3  first_diff=33
   OFF  _save_testds_to_csv                        orig=71    decomp=68    hunks=7  first_diff=19
   STRICT _on_publish_after_trading_end              [seq_len] orig=488 decomp=481
   STRICT _on_set_positions                          [seq_len] orig=297 decomp=298
   STRICT _save_testds_to_csv                        [seq_len] orig=75 decomp=68

## IQCommon/util/fileio_utils.pyc
   official 12/14  gap=2   strict 13/15  defects=2  missing=0 extra=0
   OFF  acquire                                    orig=96    decomp=93    hunks=3  first_diff=52
   OFF  write                                      orig=637   decomp=636   hunks=0  first_diff=38
   STRICT write                                      [seq_len] orig=637 decomp=636
   STRICT acquire                                    [seq_len] orig=98 decomp=93

## IQCommon/util/trade_info_utils.pyc
   official 39/40  gap=1   strict 37/41  defects=4  missing=0 extra=0
   OFF  trade_operation                            orig=304   decomp=302   hunks=2  first_diff=40
   STRICT get_trade_status                           [target_diff] #70 FOR_ITER 终点 orig=("'return_trade_info'", 'LOAD_FAST') decomp=("'count'", 'LOAD_FAST')
   STRICT get_trade_unit_info                        [seq_len] orig=240 decomp=241
   STRICT set_trade_status                           [target_diff] #113 JUMP 终点 orig=("'count'", 'LOAD_FAST') decomp=("'exchange_flag'", 'LOAD_FAST')
   STRICT trade_operation                            [seq_len] orig=304 decomp=302

## IQData/api/api_base.pyc
   official 24/25  gap=1   strict 26/27  defects=1  missing=0 extra=0
   OFF  get_history_df                             orig=1742  decomp=1742  hunks=11 first_diff=89
   STRICT get_history_df                             [seq_diff] #419 orig=('<JUMP>', 'POP_JUMP_IF_TRUE') decomp=('<JUMP>', 'POP_JUMP_IF_FALSE')

## IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc
   official 11/12  gap=1   strict 11/12  defects=1  missing=0 extra=0
   OFF  clock_worker                               orig=1275  decomp=1286  hunks=10 first_diff=481
   STRICT clock_worker                               [seq_len] orig=1276 decomp=1287

