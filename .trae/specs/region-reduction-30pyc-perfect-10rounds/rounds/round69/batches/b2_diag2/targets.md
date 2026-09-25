# diag2 targets (1 files, official gap 11, strict defects 15)

## fly/data/quote.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/fly/data/quote.pyc
   official 70/81 (gap 11)   strict 74/89 (defects 15, missing 0, extra 0)
   OFF    build_current_period_df                      orig=115   decomp=108   hunks=5  first_diff=12
   OFF    check_frequency                              orig=121   decomp=120   hunks=1  first_diff=21
   OFF    check_limit                                  orig=330   decomp=311   hunks=2  first_diff=248
   OFF    get_individual_data                          orig=312   decomp=311   hunks=1  first_diff=156
   OFF    get_price                                    orig=230   decomp=232   hunks=0  first_diff=172
   OFF    get_real_from_zeromq                         orig=703   decomp=678   hunks=0  first_diff=660
   OFF    initImagedata                                orig=243   decomp=225   hunks=0  first_diff=190
   OFF    load_bars_from_hundsun                       orig=477   decomp=483   hunks=0  first_diff=410
   OFF    load_get_price                               orig=171   decomp=171   hunks=0  first_diff=1
   OFF    run_individual_transform                     orig=362   decomp=321   hunks=2  first_diff=263
   OFF    run_tick_socket                              orig=306   decomp=307   hunks=2  first_diff=228
   STRICT build_current_period_df                      [seq_len] orig=118 decomp=109
   STRICT change_his_to_backward                       [target_diff] #213 POP_JUMP_IF_TRUE 终点 orig=("'data'", 'LOAD_FAST') decomp=('None', 'POP_TOP')
   STRICT change_his_to_forward                        [target_diff] #241 POP_JUMP_IF_FALSE 终点 orig=("'preindex'", 'LOAD_FAST') decomp=(None, 'FOR_ITER')
   STRICT check_frequency                              [seq_len] orig=123 decomp=124
   STRICT check_industry_code                          [seq_diff] #159 orig=('0', 'CONTAINS_OP') decomp=('1', 'CONTAINS_OP')
   STRICT check_limit                                  [seq_len] orig=331 decomp=311
   STRICT get_individual_data                          [seq_len] orig=314 decomp=313
   STRICT get_price                                    [seq_len] orig=230 decomp=232
   STRICT get_real_from_zeromq                         [seq_len] orig=703 decomp=678
   STRICT initImagedata                                [seq_len] orig=245 decomp=225
   STRICT load_bars_from_hundsun                       [seq_len] orig=477 decomp=483
   STRICT load_get_price                               [seq_diff] #53 orig=('<JUMP>', 'POP_JUMP_IF_FALSE') decomp=('None', 'POP_TOP')
   STRICT run_individual_transform                     [seq_len] orig=364 decomp=321
   STRICT run_tick_socket                              [seq_len] orig=309 decomp=310
   STRICT run_tick_transform                           [target_diff] #56 POP_JUMP_IF_FALSE 终点 orig=("'len'", 'LOAD_GLOBAL') decomp=("'self'", 'LOAD_FAST')
