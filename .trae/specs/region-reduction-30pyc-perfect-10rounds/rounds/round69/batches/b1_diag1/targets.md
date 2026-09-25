# diag1 targets (1 files, official gap 11, strict defects 17)

## IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc
   official 108/119 (gap 11)   strict 106/123 (defects 17, missing 0, extra 0)
   OFF    _process_cancel_order                        orig=294   decomp=293   hunks=16 first_diff=22
   OFF    _process_order                               orig=454   decomp=396   hunks=9  first_diff=349
   OFF    _sync_worker                                 orig=349   decomp=347   hunks=0  first_diff=296
   OFF    _trade_status_handle                         orig=114   decomp=112   hunks=0  first_diff=107
   OFF    after_trading_cancel_order                   orig=155   decomp=155   hunks=3  first_diff=122
   OFF    etf_basket_order                             orig=693   decomp=693   hunks=11 first_diff=216
   OFF    etf_purchase_redemption                      orig=377   decomp=369   hunks=1  first_diff=37
   OFF    get_max_amount                               orig=201   decomp=213   hunks=2  first_diff=18
   OFF    ipo_stocks_order                             orig=1075  decomp=1075  hunks=18 first_diff=278
   OFF    on_order_response                            orig=445   decomp=444   hunks=6  first_diff=57
   OFF    on_trade_response                            orig=392   decomp=391   hunks=6  first_diff=57
   STRICT _process_cancel_order                        [seq_len] orig=295 decomp=297
   STRICT _process_order                               [seq_len] orig=454 decomp=399
   STRICT _process_tick_order                          [target_diff] #27 JUMP 终点 orig=("'len'", 'LOAD_GLOBAL') decomp=("'self'", 'LOAD_FAST')
   STRICT _sync_worker                                 [seq_len] orig=350 decomp=347
   STRICT _trade_status_handle                         [seq_len] orig=114 decomp=112
   STRICT after_trading_cancel_order                   [seq_len] orig=156 decomp=159
   STRICT etf_basket_order                             [seq_diff] #254 orig=("'strategy_log'", 'LOAD_GLOBAL') decomp=("'entrust_price'", 'LOAD_FAST')
   STRICT etf_purchase_redemption                      [seq_len] orig=379 decomp=369
   STRICT get_ipo_stocks                               [target_diff] #189 POP_JUMP_IF_TRUE 终点 orig=("'str'", 'LOAD_GLOBAL') decomp=(None, 'FOR_ITER')
   STRICT get_max_amount                               [seq_len] orig=201 decomp=213
   STRICT ipo_stocks_order                             [seq_diff] #624 orig=("'new_stock'", 'LOAD_FAST') decomp=('<JUMP>', 'JUMP')
   STRICT on_order_response                            [seq_len] orig=449 decomp=448
   STRICT on_order_response_list_handle                [target_diff] #23 POP_JUMP_IF_NONE 终点 orig=("'entrust_no'", 'LOAD_FAST') decomp=(None, 'FOR_ITER')
   STRICT on_pre_before_trading_start                  [target_diff] #4 POP_JUMP_IF_FALSE 终点 orig=("'self'", 'LOAD_FAST') decomp=("'datetime'", 'LOAD_GLOBAL')
   STRICT on_trade_response                            [seq_len] orig=396 decomp=395
   STRICT on_trade_response_list_handle                [target_diff] #23 POP_JUMP_IF_NONE 终点 orig=("'entrust_no'", 'LOAD_FAST') decomp=(None, 'FOR_ITER')
   STRICT rzrq_credit_order                            [target_diff] #406 JUMP 终点 orig=("'Order'", 'LOAD_GLOBAL') decomp=("'EntrustDirection'", 'LOAD_GLOBAL')
