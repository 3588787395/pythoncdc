# R23 Decompile Report: klinedata.pyc

## Overview

| Metric | Value |
|--------|-------|
| pyc path | `F:\Downloads\pythoncdc-main\site-packages\IQCommon\api\klinedata.pyc` |
| total_functions | 63 |
| matched_functions | 25 |
| match_rate | 0.3968 (39.68%) |
| decompile_status | partial |
| previous_rate (R12) | 0.5333 |

## Pattern Distribution

| Pattern | Count | Functions |
|---------|-------|-----------|
| OTHER | 20 | <module>, <module>.get_bar_by_zmq, <module>.get_kline_by_count_new, <module>.get_kline_by_count_new.<dictcomp>, <module>.get_kline_by_count.<dictcomp>... |
| CONDITIONAL | 14 | <module>.get_history_new, <module>._all_bars_of_cache, <module>.get_kline_by_count, <module>.get_kline_by_date_new, <module>.get_exrights_data... |
| JUMP_OFFSET | 3 | <module>.get_multiminute_his_data, <module>.stk_resample_days_orderddict, <module>.get_date_and_count |
| NOP_NOISE | 1 | <module>._all_bars_of_range |

## Mismatch Details

### <module> (Pattern: OTHER)
- orig_len: 545, decomp_len: 541
- jump_diffs: 0, true_diffs: 197
- first_diff: index=263 orig=LOAD_CONST(<code object <lambda> at 0x0000019F1B21F2F0, file "./fly_docker_py311/IQCommon/a) decomp=LOAD_CONST(<code object <lambda> at 0x0000019F1B2E2A30, file "F:\Downloads\pythoncdc-main\s)

### <module>.get_history_new (Pattern: CONDITIONAL)
- orig_len: 352, decomp_len: 350
- jump_diffs: 22, true_diffs: 103
- first_diff: index=66 orig=POP_JUMP_FORWARD_IF_FALSE(1556) decomp=POP_JUMP_FORWARD_IF_FALSE(1570)

### <module>._all_bars_of_cache (Pattern: CONDITIONAL)
- orig_len: 250, decomp_len: 255
- jump_diffs: 34, true_diffs: 193
- first_diff: index=27 orig=POP_JUMP_FORWARD_IF_TRUE(160) decomp=EXTENDED_ARG(1)

### <module>.get_bar_by_zmq (Pattern: OTHER)
- orig_len: 57, decomp_len: 57
- jump_diffs: 0, true_diffs: 1
- first_diff: index=44 orig=LOAD_CONST(<code object <listcomp> at 0x0000019F1B2730F0, file "./fly_docker_py311/IQCommon) decomp=LOAD_CONST(<code object <listcomp> at 0x0000019F1B320B70, file "F:\Downloads\pythoncdc-main)

### <module>.get_kline_by_count_new (Pattern: OTHER)
- orig_len: 650, decomp_len: 638
- jump_diffs: 144, true_diffs: 489
- first_diff: index=14 orig=UNPACK_SEQUENCE(2) decomp=STORE_FAST(start_000300)

### <module>.get_kline_by_count_new.<dictcomp> (Pattern: OTHER)
- orig_len: 20, decomp_len: 20
- jump_diffs: 0, true_diffs: 1
- first_diff: index=11 orig=LOAD_CONST(<code object <listcomp> at 0x0000019F1B21F590, file "./fly_docker_py311/IQCommon) decomp=LOAD_CONST(<code object <listcomp> at 0x0000019F1B2E26B0, file "F:\Downloads\pythoncdc-main)

### <module>.get_kline_by_count (Pattern: CONDITIONAL)
- orig_len: 478, decomp_len: 470
- jump_diffs: 99, true_diffs: 377
- first_diff: index=2 orig=POP_JUMP_FORWARD_IF_NONE(18) decomp=EXTENDED_ARG(4)

### <module>.get_kline_by_count.<dictcomp> (Pattern: OTHER)
- orig_len: 20, decomp_len: 20
- jump_diffs: 0, true_diffs: 1
- first_diff: index=11 orig=LOAD_CONST(<code object <listcomp> at 0x0000019F1B21F670, file "./fly_docker_py311/IQCommon) decomp=LOAD_CONST(<code object <listcomp> at 0x0000019F1B2E2CD0, file "F:\Downloads\pythoncdc-main)

### <module>.get_kline_by_date_new (Pattern: CONDITIONAL)
- orig_len: 332, decomp_len: 321
- jump_diffs: 9, true_diffs: 28
- first_diff: index=38 orig=POP_JUMP_FORWARD_IF_NONE(386) decomp=POP_JUMP_FORWARD_IF_NONE(216)

### <module>.get_kline_by_date_new.<dictcomp> (Pattern: OTHER)
- orig_len: 20, decomp_len: 20
- jump_diffs: 0, true_diffs: 1
- first_diff: index=11 orig=LOAD_CONST(<code object <listcomp> at 0x0000019F1B21FAD0, file "./fly_docker_py311/IQCommon) decomp=LOAD_CONST(<code object <listcomp> at 0x0000019F1B2E2E90, file "F:\Downloads\pythoncdc-main)

### <module>.get_kline_by_date_one (Pattern: OTHER)
- orig_len: 193, decomp_len: 182
- jump_diffs: 7, true_diffs: 31
- first_diff: index=129 orig=LOAD_CONST(<code object <dictcomp> at 0x0000019F1B21BE30, file "./fly_docker_py311/IQCommon) decomp=LOAD_CONST(<code object <dictcomp> at 0x0000019F1B2FEF30, file "F:\Downloads\pythoncdc-main)

### <module>.get_kline_by_date_one.<dictcomp> (Pattern: OTHER)
- orig_len: 20, decomp_len: 20
- jump_diffs: 0, true_diffs: 1
- first_diff: index=11 orig=LOAD_CONST(<code object <listcomp> at 0x0000019F1B21FBB0, file "./fly_docker_py311/IQCommon) decomp=LOAD_CONST(<code object <listcomp> at 0x0000019F1B2E2BF0, file "F:\Downloads\pythoncdc-main)

### <module>._all_bars_of_range (Pattern: NOP_NOISE)
- orig_len: 17, decomp_len: 16
- jump_diffs: 0, true_diffs: 3
- first_diff: index=14 orig=NOP(None) decomp=LOAD_FAST(data_array)

### <module>.get_multiminute_his_data (Pattern: JUMP_OFFSET)
- orig_len: 535, decomp_len: 439
- jump_diffs: 34, true_diffs: 244
- first_diff: index=18 orig=EXTENDED_ARG(5) decomp=EXTENDED_ARG(3)

### <module>.get_multiminute_his_data_by_date (Pattern: OTHER)
- orig_len: 611, decomp_len: 614
- jump_diffs: 15, true_diffs: 124
- first_diff: index=293 orig=JUMP_FORWARD(3222) decomp=JUMP_FORWARD(3228)

### <module>.kline_datetime_list (Pattern: OTHER)
- orig_len: 413, decomp_len: 390
- jump_diffs: 59, true_diffs: 208
- first_diff: index=72 orig=JUMP_FORWARD(1704) decomp=JUMP_FORWARD(1616)

### <module>.get_exrights_data (Pattern: CONDITIONAL)
- orig_len: 255, decomp_len: 261
- jump_diffs: 20, true_diffs: 137
- first_diff: index=60 orig=POP_JUMP_FORWARD_IF_FALSE(844) decomp=POP_JUMP_FORWARD_IF_FALSE(868)

### <module>.get_kline_by_date_ndarray (Pattern: CONDITIONAL)
- orig_len: 239, decomp_len: 209
- jump_diffs: 17, true_diffs: 107
- first_diff: index=47 orig=POP_JUMP_FORWARD_IF_TRUE(656) decomp=POP_JUMP_FORWARD_IF_TRUE(308)

### <module>.get_all_real_minute_kline (Pattern: OTHER)
- orig_len: 305, decomp_len: 306
- jump_diffs: 38, true_diffs: 233
- first_diff: index=29 orig=FOR_ITER(1530) decomp=FOR_ITER(1532)

### <module>.get_all_real_minute_kline.<dictcomp> (Pattern: OTHER)
- orig_len: 20, decomp_len: 20
- jump_diffs: 0, true_diffs: 1
- first_diff: index=11 orig=LOAD_CONST(<code object <listcomp> at 0x0000019F1B2E0030, file "./fly_docker_py311/IQCommon) decomp=LOAD_CONST(<code object <listcomp> at 0x0000019F1B2E2DB0, file "F:\Downloads\pythoncdc-main)

### <module>.klineCacheData_to_dict (Pattern: OTHER)
- orig_len: 216, decomp_len: 215
- jump_diffs: 29, true_diffs: 156
- first_diff: index=29 orig=FOR_ITER(1108) decomp=FOR_ITER(1102)

### <module>.klineCacheData_to_dict.<dictcomp> (Pattern: OTHER)
- orig_len: 20, decomp_len: 20
- jump_diffs: 0, true_diffs: 1
- first_diff: index=11 orig=LOAD_CONST(<code object <listcomp> at 0x0000019F1B2E0F10, file "./fly_docker_py311/IQCommon) decomp=LOAD_CONST(<code object <listcomp> at 0x0000019F1B2E3210, file "F:\Downloads\pythoncdc-main)

### <module>.get_post_data (Pattern: OTHER)
- orig_len: 84, decomp_len: 84
- jump_diffs: 0, true_diffs: 1
- first_diff: index=70 orig=LOAD_CONST(<code object <listcomp> at 0x0000019F1B2735A0, file "./fly_docker_py311/IQCommon) decomp=LOAD_CONST(<code object <listcomp> at 0x0000019F1B3212F0, file "F:\Downloads\pythoncdc-main)

### <module>.get_all_real_daily_kline (Pattern: OTHER)
- orig_len: 216, decomp_len: 215
- jump_diffs: 35, true_diffs: 159
- first_diff: index=17 orig=FOR_ITER(1044) decomp=FOR_ITER(1042)

### <module>.get_all_real_daily_kline.<dictcomp> (Pattern: OTHER)
- orig_len: 20, decomp_len: 20
- jump_diffs: 0, true_diffs: 1
- first_diff: index=11 orig=LOAD_CONST(<code object <listcomp> at 0x0000019F1B2E0FF0, file "./fly_docker_py311/IQCommon) decomp=LOAD_CONST(<code object <listcomp> at 0x0000019F1B2E3130, file "F:\Downloads\pythoncdc-main)

### <module>.get_history_common (Pattern: CONDITIONAL)
- orig_len: 536, decomp_len: 536
- jump_diffs: 63, true_diffs: 355
- first_diff: index=111 orig=POP_JUMP_FORWARD_IF_NOT_NONE(760) decomp=EXTENDED_ARG(3)

### <module>.get_price_common (Pattern: CONDITIONAL)
- orig_len: 594, decomp_len: 600
- jump_diffs: 106, true_diffs: 465
- first_diff: index=26 orig=POP_JUMP_FORWARD_IF_FALSE(280) decomp=EXTENDED_ARG(5)

### <module>.stk_history_day_complex (Pattern: OTHER)
- orig_len: 211, decomp_len: 211
- jump_diffs: 0, true_diffs: 1
- first_diff: index=26 orig=LOAD_CONST(<code object <listcomp> at 0x0000019F1B273690, file "./fly_docker_py311/IQCommon) decomp=LOAD_CONST(<code object <listcomp> at 0x0000019F1B3213E0, file "F:\Downloads\pythoncdc-main)

### <module>.stk_resample_days_bars (Pattern: CONDITIONAL)
- orig_len: 260, decomp_len: 151
- jump_diffs: 1, true_diffs: 123
- first_diff: index=122 orig=POP_JUMP_FORWARD_IF_FALSE(690) decomp=POP_JUMP_FORWARD_IF_FALSE(694)

### <module>.get_history_date_and_count_ifalse (Pattern: OTHER)
- orig_len: 468, decomp_len: 460
- jump_diffs: 47, true_diffs: 313
- first_diff: index=71 orig=JUMP_FORWARD(2346) decomp=JUMP_FORWARD(2282)

### <module>.get_history_date_and_count_itrue (Pattern: CONDITIONAL)
- orig_len: 438, decomp_len: 472
- jump_diffs: 59, true_diffs: 351
- first_diff: index=4 orig=POP_JUMP_FORWARD_IF_FALSE(362) decomp=POP_JUMP_FORWARD_IF_FALSE(348)

### <module>.stk_resample_days_orderddict (Pattern: JUMP_OFFSET)
- orig_len: 295, decomp_len: 183
- jump_diffs: 6, true_diffs: 151
- first_diff: index=31 orig=EXTENDED_ARG(2) decomp=EXTENDED_ARG(1)

### <module>._is_same_type_date (Pattern: CONDITIONAL)
- orig_len: 99, decomp_len: 98
- jump_diffs: 18, true_diffs: 49
- first_diff: index=4 orig=POP_JUMP_FORWARD_IF_FALSE(174) decomp=POP_JUMP_FORWARD_IF_FALSE(172)

### <module>.get_date_and_count (Pattern: JUMP_OFFSET)
- orig_len: 776, decomp_len: 741
- jump_diffs: 74, true_diffs: 503
- first_diff: index=165 orig=EXTENDED_ARG(1) decomp=EXTENDED_ARG(5)

### <module>.np_tp_pd (Pattern: CONDITIONAL)
- orig_len: 189, decomp_len: 190
- jump_diffs: 15, true_diffs: 120
- first_diff: index=24 orig=POP_JUMP_FORWARD_IF_FALSE(340) decomp=POP_JUMP_FORWARD_IF_FALSE(342)

### <module>._align_data_to_benchmark (Pattern: OTHER)
- orig_len: 138, decomp_len: 138
- jump_diffs: 0, true_diffs: 2
- first_diff: index=23 orig=LOAD_CONST(<code object <dictcomp> at 0x0000019F1B2E11B0, file "./fly_docker_py311/IQCommon) decomp=LOAD_CONST(<code object <dictcomp> at 0x0000019F1B2E3670, file "F:\Downloads\pythoncdc-main)

### <module>.to_pd_result (Pattern: CONDITIONAL)
- orig_len: 215, decomp_len: 219
- jump_diffs: 15, true_diffs: 167
- first_diff: index=35 orig=POP_JUMP_FORWARD_IF_NOT_NONE(648) decomp=EXTENDED_ARG(1)

### <module>.check_datetime_common (Pattern: CONDITIONAL)
- orig_len: 254, decomp_len: 256
- jump_diffs: 22, true_diffs: 161
- first_diff: index=62 orig=POP_JUMP_FORWARD_IF_FALSE(480) decomp=POP_JUMP_FORWARD_IF_FALSE(632)
