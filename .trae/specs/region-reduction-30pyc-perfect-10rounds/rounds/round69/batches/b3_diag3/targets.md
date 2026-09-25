# diag3 targets (3 files, official gap 5, strict defects 8)

## IQCommon/api/klinedata.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc
   official 43/45 (gap 2)   strict 58/63 (defects 5, missing 0, extra 0)
   OFF    get_multiminute_his_data                     orig=479   decomp=478   hunks=3  first_diff=16
   OFF    kline_datetime_list                          orig=389   decomp=389   hunks=9  first_diff=228
   STRICT get_history_common                           [target_diff] #41 POP_JUMP_IF_NONE 终点 orig=("'is_dict'", 'LOAD_FAST') decomp=("'fields'", 'LOAD_FAST')
   STRICT get_kline_by_count_new                       [target_diff] #161 POP_JUMP_IF_NONE 终点 orig=('0', 'LOAD_CONST') decomp=("'symbols'", 'LOAD_FAST')
   STRICT get_multiminute_his_data                     [seq_len] orig=481 decomp=482
   STRICT get_price_common                             [target_diff] #114 POP_JUMP_IF_NONE 终点 orig=("'frequency'", 'LOAD_FAST') decomp=("'is_dict'", 'LOAD_FAST')
   STRICT kline_datetime_list                          [seq_diff] #151 orig=('<JUMP>', 'POP_JUMP_IF_TRUE') decomp=('<JUMP>', 'POP_JUMP_IF_FALSE')

## IQCommon/util/fileio_utils.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQCommon/util/fileio_utils.pyc
   official 12/14 (gap 2)   strict 13/15 (defects 2, missing 0, extra 0)
   OFF    acquire                                      orig=96    decomp=93    hunks=3  first_diff=52
   OFF    write                                        orig=637   decomp=636   hunks=0  first_diff=38
   STRICT write                                        [seq_len] orig=637 decomp=636
   STRICT acquire                                      [seq_len] orig=98 decomp=93

## IQData/api/api_base.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQData/api/api_base.pyc
   official 24/25 (gap 1)   strict 26/27 (defects 1, missing 0, extra 0)
   OFF    get_history_df                               orig=1742  decomp=1742  hunks=11 first_diff=89
   STRICT get_history_df                               [seq_diff] #419 orig=('<JUMP>', 'POP_JUMP_IF_TRUE') decomp=('<JUMP>', 'POP_JUMP_IF_FALSE')
