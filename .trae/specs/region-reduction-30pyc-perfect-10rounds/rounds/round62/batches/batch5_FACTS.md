# Batch 5 facts (measured core/cfg/region_ast_generator.py sha fa0808ca3766b5150dcf, Fix1+Fix2 landed / Fix3 reverted
)

## site-packages/IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc
- index(r61): partial 32/34  landed: 32/34  deficit 2
- `future_order` orig=101 decomp=92 delta=-9 jump_diffs=2 true_diffs=36
    first_diff: {"index": 62, "orig_op": "LOAD_GLOBAL", "decomp_op": "LOAD_FAST", "orig_arg": "strategy_log", "decomp_arg": "order_"}
- `option_order` orig=83 decomp=73 delta=-10 jump_diffs=3 true_diffs=39
    first_diff: {"index": 33, "orig_op": "LOAD_GLOBAL", "decomp_op": "LOAD_FAST", "orig_arg": "strategy_log", "decomp_arg": "order_"}

## site-packages/fly/logger.pyc
- index(r61): partial 28/30  landed: 28/30  deficit 2
- `logging_process` orig=99 decomp=95 delta=-4 jump_diffs=2 true_diffs=62
    first_diff: {"index": 36, "orig_op": "LOAD_FAST", "decomp_op": "LOAD_FAST", "orig_arg": "thread_event", "decomp_arg": "self"}
- `write_logging_thread` orig=113 decomp=113 delta=0 jump_diffs=1 true_diffs=40
    first_diff: {"index": 71, "orig_op": "LOAD_FAST", "decomp_op": "JUMP_FORWARD", "orig_arg": "msgs", "decomp_arg": 612}

## site-packages/fly/simtradding/flyAccount.pyc
- index(r61): partial 21/23  landed: 21/23  deficit 2
- `_do_request` orig=436 decomp=429 delta=-7 jump_diffs=2 true_diffs=379
    first_diff: {"index": 54, "orig_op": "RETURN_VALUE", "decomp_op": "POP_TOP", "orig_arg": null, "decomp_arg": null}
- `init_connection` orig=42 decomp=41 delta=-1 jump_diffs=0 true_diffs=25
    first_diff: {"index": 16, "orig_op": "POP_JUMP_FORWARD_IF_FALSE", "decomp_op": "POP_JUMP_FORWARD_IF_TRUE", "orig_arg": 172, "decomp_arg": 102}

## site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc
- index(r61): partial 11/12  landed: 11/12  deficit 1
- `clock_worker` orig=1275 decomp=1286 delta=11 jump_diffs=10 true_diffs=481
    first_diff: {"index": 794, "orig_op": "LOAD_FAST", "decomp_op": "JUMP_FORWARD", "orig_arg": "now_date", "decomp_arg": 6750}

## site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc
- index(r61): partial 16/17  landed: 16/17  deficit 1
- `match` orig=713 decomp=689 delta=-24 jump_diffs=9 true_diffs=524
    first_diff: {"index": 182, "orig_op": "JUMP_FORWARD", "decomp_op": "LOAD_FAST", "orig_arg": 2464, "decomp_arg": "self"}

