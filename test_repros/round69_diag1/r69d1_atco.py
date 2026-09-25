# r69diag1 synth witness: shared-block (chain merge) absorbed as elif_final_else.
# Shape matches trade_live_broker.after_trading_cancel_order:
#   the block that starts the SECOND, independent `if` is reached by
#   (a) the elif condition's false exit, (b) the for-loop FOR_ITER exit,
#   (c) the break JUMP_FORWARD -- i.e. it is the if/elif chain's MERGE.
def r69d1_atco(order_param, orders):
    if order_param is None:
        return None
    elif isinstance(order_param, str):
        for order in orders:
            if order_param == order.oid:
                order_param = order
                break
    if isinstance(order_param, str):
        return None
    else:
        return order_param.no
