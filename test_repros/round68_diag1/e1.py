# -*- coding: utf-8 -*-
"""Round 68 diag1 synthetic reproduction: elif-chain seam absorbed a loop exit.

Trimmed copy of TradeLiveBroker.after_trading_cancel_order (trade_live_broker.pyc).
Three SEQUENTIAL statements whose 1st arm ends in `return` (so the compiler makes
the false edge land exactly on the next test, indistinguishable from `elif`), whose
2nd statement's arm is a `for` loop with a `break`, and whose 3rd statement is an
if/else.  A correct decompile cannot fold statement 3 into the chain of 1-2, because
the loop exit falls *through* into statement 3's test instead of jumping over it.

Also included: a control case that really IS an if/elif/else chain (c1) so the
candidate cannot be judged on a single sample.
"""

strategy_log = None
_ = lambda s: s


def e1(order_param, orders):
    if order_param is None:
        strategy_log.warning('none')
        return None
    if isinstance(order_param, str):
        for order in orders:
            if order_param == order.order_id:
                order_param = order
                break
    if isinstance(order_param, str):
        return None
    else:
        return order_param.entrust_no


def c1(order_param, orders):
    if order_param is None:
        strategy_log.warning('none')
    elif isinstance(order_param, str):
        for order in orders:
            if order_param == order.order_id:
                order_param = order
                break
        strategy_log.info('after-loop')
    else:
        return order_param.entrust_no
    return 'tail'
