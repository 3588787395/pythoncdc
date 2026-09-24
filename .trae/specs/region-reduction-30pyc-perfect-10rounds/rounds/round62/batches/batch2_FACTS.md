# Batch 2 facts (measured core/cfg/region_ast_generator.py sha fa0808ca3766b5150dcf, Fix1+Fix2 landed / Fix3 reverted
)

## site-packages/fly/data/quote.pyc
- index(r61): partial 70/81  landed: 70/81  deficit 11
- `build_current_period_df` orig=115 decomp=108 delta=-7 jump_diffs=5 true_diffs=12
    first_diff: {"index": 103, "orig_op": "LOAD_FAST", "decomp_op": "POP_TOP", "orig_arg": "tempdict", "decomp_arg": null}
- `check_frequency` orig=121 decomp=120 delta=-1 jump_diffs=1 true_diffs=21
    first_diff: {"index": 100, "orig_op": "LOAD_CONST", "decomp_op": "JUMP_FORWARD", "orig_arg": null, "decomp_arg": 558}
- `check_limit` orig=330 decomp=311 delta=-19 jump_diffs=2 true_diffs=248
    first_diff: {"index": 50, "orig_op": "LOAD_ATTR", "decomp_op": "LOAD_METHOD", "orig_arg": "log", "decomp_arg": "api_get_from_zeromq"}
- `get_individual_data` orig=312 decomp=311 delta=-1 jump_diffs=1 true_diffs=156
    first_diff: {"index": 155, "orig_op": "JUMP_FORWARD", "decomp_op": "LOAD_FAST", "orig_arg": 1124, "decomp_arg": "redata"}
- `get_price` orig=230 decomp=188 delta=-42 jump_diffs=0 true_diffs=227
    first_diff: {"index": 1, "orig_op": "LOAD_FAST", "decomp_op": "LOAD_CONST", "orig_arg": "self", "decomp_arg": "self调用函数get_price，参数为：stocks=securityNone"}
- `get_real_from_zeromq` orig=703 decomp=678 delta=-25 jump_diffs=0 true_diffs=660
    first_diff: {"index": 33, "orig_op": "LOAD_ATTR", "decomp_op": "LOAD_METHOD", "orig_arg": "log", "decomp_arg": "api_get_from_multi_zeromq"}
- `initImagedata` orig=243 decomp=225 delta=-18 jump_diffs=0 true_diffs=190
    first_diff: {"index": 35, "orig_op": "LOAD_ATTR", "decomp_op": "LOAD_METHOD", "orig_arg": "log", "decomp_arg": "api_get_from_multi_zeromq"}
- `load_bars_from_hundsun` orig=477 decomp=470 delta=-7 jump_diffs=0 true_diffs=464
    first_diff: {"index": 1, "orig_op": "LOAD_FAST", "decomp_op": "LOAD_CONST", "orig_arg": "self", "decomp_arg": "self调用函数load_bars_from_hundsun，参数为：stocks=stocksNone"}
- `load_get_price` orig=171 decomp=136 delta=-35 jump_diffs=1 true_diffs=167
    first_diff: {"index": 1, "orig_op": "LOAD_FAST", "decomp_op": "LOAD_CONST", "orig_arg": "self", "decomp_arg": "self调用函数load_get_price，参数为：stocks=stocksNone"}
- `run_individual_transform` orig=362 decomp=321 delta=-41 jump_diffs=2 true_diffs=263
    first_diff: {"index": 93, "orig_op": "LOAD_FAST", "decomp_op": "JUMP_FORWARD", "orig_arg": "socket", "decomp_arg": 940}
- `run_tick_socket` orig=306 decomp=307 delta=1 jump_diffs=2 true_diffs=228
    first_diff: {"index": 79, "orig_op": "LOAD_FAST", "decomp_op": "LOAD_GLOBAL", "orig_arg": "self", "decomp_arg": "list"}

## site-packages/IQData/plugins/plugin_system_realquote/real_quote.pyc
- index(r61): partial 39/44  landed: 39/44  deficit 5
- `get_cache_l2_data` orig=337 decomp=335 delta=-2 jump_diffs=2 true_diffs=313
    first_diff: {"index": 18, "orig_op": "JUMP_FORWARD", "decomp_op": "POP_TOP", "orig_arg": 92, "decomp_arg": null}
- `get_cache_l2_data_by_one` orig=321 decomp=320 delta=-1 jump_diffs=2 true_diffs=300
    first_diff: {"index": 18, "orig_op": "JUMP_FORWARD", "decomp_op": "POP_TOP", "orig_arg": 92, "decomp_arg": null}
- `get_real_minute_kline` orig=253 decomp=254 delta=1 jump_diffs=3 true_diffs=197
    first_diff: {"index": 56, "orig_op": "JUMP_FORWARD", "decomp_op": "LOAD_FAST", "orig_arg": 570, "decomp_arg": "fq"}
- `get_tick_direction` orig=259 decomp=258 delta=-1 jump_diffs=3 true_diffs=102
    first_diff: {"index": 149, "orig_op": "JUMP_FORWARD", "decomp_op": "LOAD_FAST", "orig_arg": 1106, "decomp_arg": "redata"}
- `one_prod_to_ndarray` orig=605 decomp=607 delta=2 jump_diffs=5 true_diffs=424
    first_diff: {"index": 136, "orig_op": "JUMP_FORWARD", "decomp_op": "LOAD_FAST", "orig_arg": 1530, "decomp_arg": "data_dict"}

## site-packages/IQCommon/common/main.pyc
- index(r61): partial 29/33  landed: 29/33  deficit 4
- **MISSING from product** (function absent): ['<dictcomp>', '<lambda>']
- `get_same_shard_server_ip_info` orig=192 decomp=173 delta=-19 jump_diffs=11 true_diffs=62
    first_diff: {"index": 80, "orig_op": "STORE_DEREF", "decomp_op": "STORE_FAST", "orig_arg": "local_server_shard", "decomp_arg": "local_server_shard"}
- `get_server_ip_info` orig=194 decomp=166 delta=-28 jump_diffs=9 true_diffs=71
    first_diff: {"index": 82, "orig_op": "STORE_DEREF", "decomp_op": "STORE_FAST", "orig_arg": "local_server_shard", "decomp_arg": "local_server_shard"}

## site-packages/fly/data/quote_handler.pyc
- index(r61): partial 55/57  landed: 55/57  deficit 2
- `get_kline_binary` orig=129 decomp=128 delta=-1 jump_diffs=3 true_diffs=58
    first_diff: {"index": 71, "orig_op": "JUMP_FORWARD", "decomp_op": "LOAD_FAST", "orig_arg": 330, "decomp_arg": "columns"}
- `get_kline_local` orig=760 decomp=682 delta=-78 jump_diffs=12 true_diffs=547
    first_diff: {"index": 210, "orig_op": "LOAD_GLOBAL", "decomp_op": "JUMP_FORWARD", "orig_arg": "int", "decomp_arg": 2426}

