# Batch 1 facts (measured core/cfg/region_ast_generator.py sha fa0808ca3766b5150dcf, Fix1+Fix2 landed / Fix3 reverted
)

## site-packages/IQEngine/plugins/plugin_system_log/__init__.pyc
- index(r61): partial 9/10  landed: 9/10  deficit 1
- `setup` orig=320 decomp=313 delta=-7 jump_diffs=1 true_diffs=199
    first_diff: {"index": 118, "orig_op": "LOAD_GLOBAL", "decomp_op": "LOAD_GLOBAL", "orig_arg": "LogEngine", "decomp_arg": "user_log"}

## site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc
- index(r61): partial 104/119  landed: 104/119  deficit 15
- `_process_cancel_order` orig=293 decomp=292 delta=-1 jump_diffs=16 true_diffs=43
    first_diff: {"index": 246, "orig_op": "JUMP_FORWARD", "decomp_op": "LOAD_GLOBAL", "orig_arg": 2000, "decomp_arg": "strategy_log"}
- `_process_order` orig=454 decomp=396 delta=-58 jump_diffs=9 true_diffs=349
    first_diff: {"index": 95, "orig_op": "JUMP_BACKWARD", "decomp_op": "JUMP_FORWARD", "orig_arg": 44, "decomp_arg": 2666}
- `_sync_worker` orig=349 decomp=347 delta=-2 jump_diffs=0 true_diffs=296
    first_diff: {"index": 48, "orig_op": "POP_JUMP_FORWARD_IF_TRUE", "decomp_op": "POP_JUMP_FORWARD_IF_FALSE", "orig_arg": 704, "decomp_arg": 562}
- `_trade_status_handle` orig=114 decomp=112 delta=-2 jump_diffs=0 true_diffs=107
    first_diff: {"index": 6, "orig_op": "LOAD_GLOBAL", "decomp_op": "LOAD_FAST", "orig_arg": "get_trade_status", "decomp_arg": "self"}
- `after_trading_cancel_order` orig=155 decomp=155 delta=0 jump_diffs=3 true_diffs=122
    first_diff: {"index": 31, "orig_op": "LOAD_GLOBAL", "decomp_op": "LOAD_CONST", "orig_arg": "isinstance", "decomp_arg": null}
- `etf_basket_order` orig=693 decomp=693 delta=0 jump_diffs=11 true_diffs=216
    first_diff: {"index": 254, "orig_op": "LOAD_GLOBAL", "decomp_op": "LOAD_FAST", "orig_arg": "strategy_log", "decomp_arg": "entrust_price"}
- `etf_purchase_redemption` orig=377 decomp=355 delta=-22 jump_diffs=2 true_diffs=100
    first_diff: {"index": 274, "orig_op": "LOAD_GLOBAL", "decomp_op": "LOAD_CONST", "orig_arg": "strategy_log", "decomp_arg": "strategy_log后端服务 "}
- `fund_transfer` orig=123 decomp=88 delta=-35 jump_diffs=1 true_diffs=57
    first_diff: {"index": 66, "orig_op": "LOAD_GLOBAL", "decomp_op": "LOAD_FAST", "orig_arg": "strategy_log", "decomp_arg": "trans_direction"}
- `get_all_orders` orig=79 decomp=78 delta=-1 jump_diffs=2 true_diffs=24
    first_diff: {"index": 55, "orig_op": "JUMP_FORWARD", "decomp_op": "LOAD_DEREF", "orig_arg": 362, "decomp_arg": "security"}
- `get_etf_stock_info` orig=144 decomp=117 delta=-27 jump_diffs=1 true_diffs=139
    first_diff: {"index": 5, "orig_op": "JUMP_FORWARD", "decomp_op": "BUILD_LIST", "orig_arg": 56, "decomp_arg": 0}
- `get_max_amount` orig=201 decomp=213 delta=12 jump_diffs=2 true_diffs=18
    first_diff: {"index": 195, "orig_op": "LOAD_FAST", "decomp_op": "JUMP_FORWARD", "orig_arg": "max_amount", "decomp_arg": 1124}
- `ipo_stocks_order` orig=1075 decomp=1076 delta=1 jump_diffs=10 true_diffs=437
    first_diff: {"index": 594, "orig_op": "JUMP_FORWARD", "decomp_op": "JUMP_BACKWARD", "orig_arg": 3378, "decomp_arg": 2380}
- `market_fund_transfer` orig=94 decomp=67 delta=-27 jump_diffs=1 true_diffs=41
    first_diff: {"index": 53, "orig_op": "LOAD_GLOBAL", "decomp_op": "LOAD_CONST", "orig_arg": "strategy_log", "decomp_arg": "strategy_log转入"}
- `on_order_response` orig=445 decomp=444 delta=-1 jump_diffs=6 true_diffs=57
    first_diff: {"index": 386, "orig_op": "LOAD_FAST", "decomp_op": "LOAD_GLOBAL", "orig_arg": "receive_other_response", "decomp_arg": "system_log"}
- `on_trade_response` orig=392 decomp=391 delta=-1 jump_diffs=6 true_diffs=57
    first_diff: {"index": 333, "orig_op": "LOAD_FAST", "decomp_op": "LOAD_GLOBAL", "orig_arg": "receive_other_response", "decomp_arg": "system_log"}

