# Batch 3 facts (measured core/cfg/region_ast_generator.py sha fa0808ca3766b5150dcf, Fix1+Fix2 landed / Fix3 reverted
)

## site-packages/IQCommon/api/klinedata.pyc
- index(r61): partial 42/45  landed: 42/45  deficit 3
- `get_all_real_daily_kline` orig=188 decomp=187 delta=-1 jump_diffs=3 true_diffs=26
    first_diff: {"index": 162, "orig_op": "JUMP_BACKWARD", "decomp_op": "PUSH_EXC_INFO", "orig_arg": 86, "decomp_arg": null}
- `get_multiminute_his_data` orig=479 decomp=478 delta=-1 jump_diffs=3 true_diffs=16
    first_diff: {"index": 463, "orig_op": "JUMP_FORWARD", "decomp_op": "LOAD_FAST", "orig_arg": 2758, "decomp_arg": "his_data_dict"}
- `kline_datetime_list` orig=389 decomp=389 delta=0 jump_diffs=9 true_diffs=228
    first_diff: {"index": 150, "orig_op": "POP_JUMP_FORWARD_IF_TRUE", "decomp_op": "POP_JUMP_FORWARD_IF_FALSE", "orig_arg": 666, "decomp_arg": 1702}

## site-packages/IQCommon/util/common_func.pyc
- index(r61): partial 18/21  landed: 18/21  deficit 3
- `get_crontab_execute_time` orig=93 decomp=81 delta=-12 jump_diffs=2 true_diffs=48
    first_diff: {"index": 45, "orig_op": "LOAD_FAST", "decomp_op": "LOAD_GLOBAL", "orig_arg": "script_time_info", "decomp_arg": "hour_info"}
- `get_kline_time_by_frequency_array` orig=231 decomp=228 delta=-3 jump_diffs=0 true_diffs=45
    first_diff: {"index": 185, "orig_op": "LOAD_FAST", "decomp_op": "LOAD_GLOBAL", "orig_arg": "freq_k_minute", "decomp_arg": "np"}
- `get_kline_time_by_section` orig=210 decomp=190 delta=-20 jump_diffs=0 true_diffs=84
    first_diff: {"index": 124, "orig_op": "LOAD_CONST", "decomp_op": "POP_JUMP_FORWARD_IF_FALSE", "orig_arg": null, "decomp_arg": 596}

## site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc
- index(r61): partial 32/35  landed: 32/35  deficit 3
- `_on_publish_after_trading_end` orig=486 decomp=481 delta=-5 jump_diffs=3 true_diffs=33
    first_diff: {"index": 453, "orig_op": "JUMP_FORWARD", "decomp_op": "LOAD_FAST", "orig_arg": 2808, "decomp_arg": "self"}
- `_save_testds_to_csv` orig=71 decomp=68 delta=-3 jump_diffs=7 true_diffs=19
    first_diff: {"index": 33, "orig_op": "JUMP_BACKWARD", "decomp_op": "JUMP_FORWARD", "orig_arg": 108, "decomp_arg": 220}
- `get_TradeMode_trades` orig=1839 decomp=1753 delta=-86 jump_diffs=4 true_diffs=1620
    first_diff: {"index": 183, "orig_op": "COPY", "decomp_op": "LOAD_CONST", "orig_arg": 2, "decomp_arg": 1}

## site-packages/IQEngine/utils/scheduler.pyc
- index(r61): partial 42/45  landed: 42/45  deficit 3
- `get_checked_time` orig=106 decomp=106 delta=0 jump_diffs=0 true_diffs=43
    first_diff: {"index": 18, "orig_op": "LOAD_GLOBAL", "decomp_op": "JUMP_FORWARD", "orig_arg": "divmod", "decomp_arg": 352}
- `is_run_interval_time_now` orig=225 decomp=201 delta=-24 jump_diffs=2 true_diffs=173
    first_diff: {"index": 51, "orig_op": "JUMP_FORWARD", "decomp_op": "LOAD_CONST", "orig_arg": 410, "decomp_arg": null}
- `run_daily` orig=77 decomp=71 delta=-6 jump_diffs=0 true_diffs=56
    first_diff: {"index": 21, "orig_op": "LOAD_GLOBAL", "decomp_op": "STORE_DEREF", "orig_arg": "int", "decomp_arg": "hour"}

## site-packages/IQCommon/graph.pyc
- index(r61): partial 29/31  landed: 29/31  deficit 2
- `_get_influence_task` orig=207 decomp=195 delta=-12 jump_diffs=2 true_diffs=124
    first_diff: {"index": 80, "orig_op": "LOAD_FAST", "decomp_op": "LOAD_FAST", "orig_arg": "error_return", "decomp_arg": "error_dict"}
- `_process_task_queue` orig=378 decomp=378 delta=0 jump_diffs=1 true_diffs=118
    first_diff: {"index": 119, "orig_op": "LOAD_CONST", "decomp_op": "JUMP_FORWARD", "orig_arg": null, "decomp_arg": 842}

