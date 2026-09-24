# Batch 4 facts (measured core/cfg/region_ast_generator.py sha fa0808ca3766b5150dcf, Fix1+Fix2 landed / Fix3 reverted
)

## site-packages/IQCommon/strategy/wizard_quant_api.pyc
- index(r61): partial 51/53  landed: 51/53  deficit 2
- `calculate_di` orig=75 decomp=73 delta=-2 jump_diffs=0 true_diffs=45
    first_diff: {"index": 29, "orig_op": "LOAD_CLOSURE", "decomp_op": "BUILD_TUPLE", "orig_arg": "low", "decomp_arg": 1}
- `params_analysis` orig=133 decomp=126 delta=-7 jump_diffs=1 true_diffs=117
    first_diff: {"index": 14, "orig_op": "JUMP_FORWARD", "decomp_op": "LOAD_CONST", "orig_arg": 48, "decomp_arg": null}

## site-packages/IQCommon/util/trade_info_utils.pyc
- index(r61): partial 38/40  landed: 38/40  deficit 2
- `get_trade_list` orig=339 decomp=323 delta=-16 jump_diffs=14 true_diffs=148
    first_diff: {"index": 157, "orig_op": "LOAD_FAST", "decomp_op": "LOAD_FAST", "orig_arg": "item", "decomp_arg": "trades"}
- `trade_operation` orig=304 decomp=302 delta=-2 jump_diffs=2 true_diffs=40
    first_diff: {"index": 264, "orig_op": "LOAD_CONST", "decomp_op": "LOAD_GLOBAL", "orig_arg": null, "decomp_arg": "app_log"}

## site-packages/IQData/api/api_base.pyc
- index(r61): partial 23/25  landed: 23/25  deficit 2
- `get_future_history_df` orig=973 decomp=957 delta=-16 jump_diffs=3 true_diffs=229
    first_diff: {"index": 742, "orig_op": "LOAD_GLOBAL", "decomp_op": "LOAD_FAST", "orig_arg": "len", "decomp_arg": "engine_obj"}
- `get_history_df` orig=1742 decomp=1719 delta=-23 jump_diffs=14 true_diffs=1277
    first_diff: {"index": 419, "orig_op": "POP_JUMP_FORWARD_IF_TRUE", "decomp_op": "POP_JUMP_FORWARD_IF_FALSE", "orig_arg": 2254, "decomp_arg": 2570}

## site-packages/IQData/plugins/plugin_system_fly_historyquote/history_data_source.pyc
- index(r61): partial 16/18  landed: 16/18  deficit 2
- `get_kline_by_count` orig=854 decomp=841 delta=-13 jump_diffs=3 true_diffs=807
    first_diff: {"index": 19, "orig_op": "POP_JUMP_FORWARD_IF_FALSE", "decomp_op": "POP_JUMP_FORWARD_IF_TRUE", "orig_arg": 172, "decomp_arg": 132}
- `get_price` orig=550 decomp=544 delta=-6 jump_diffs=4 true_diffs=475
    first_diff: {"index": 62, "orig_op": "LOAD_FAST", "decomp_op": "LOAD_FAST", "orig_arg": "fields", "decomp_arg": "fq"}

## site-packages/IQData/utils/common_func.pyc
- index(r61): partial 22/24  landed: 22/24  deficit 2
- `get_kline_time_by_section` orig=210 decomp=190 delta=-20 jump_diffs=0 true_diffs=84
    first_diff: {"index": 124, "orig_op": "LOAD_CONST", "decomp_op": "POP_JUMP_FORWARD_IF_FALSE", "orig_arg": null, "decomp_arg": 596}
- `handle_exrights` orig=276 decomp=268 delta=-8 jump_diffs=1 true_diffs=263
    first_diff: {"index": 7, "orig_op": "LOAD_GLOBAL", "decomp_op": "LOAD_FAST", "orig_arg": "len", "decomp_arg": "tmp_dividends"}

## site-packages/IQCommon/util/fileio_utils.pyc
- index(r61): partial 12/14  landed: 12/14  deficit 2
- `acquire` orig=96 decomp=93 delta=-3 jump_diffs=3 true_diffs=52
    first_diff: {"index": 40, "orig_op": "LOAD_GLOBAL", "decomp_op": "JUMP_FORWARD", "orig_arg": "os", "decomp_arg": 354}
- `write` orig=637 decomp=637 delta=0 jump_diffs=4 true_diffs=519
    first_diff: {"index": 42, "orig_op": "LOAD_CONST", "decomp_op": "JUMP_FORWARD", "orig_arg": null, "decomp_arg": 778}

