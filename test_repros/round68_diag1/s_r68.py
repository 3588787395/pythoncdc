# -*- coding: utf-8 -*-
"""Round 68 diag1 synthetic reproduction (r68).

Shapes are trimmed copies of `etf_purchase_redemption` / `_process_order` in
site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc .
Compiled with the local CPython 3.11.7 (magic 0xa70d, same as the target pyc).

S1: an f-string with N attribute interpolations, whose LAST field contains an
    inline ternary, passed as the argument of a cross-block pending call
    `strategy_log.info(_(f"..."))`  ->  merge_ctx == 'fstring'.
S2: same but the value is stored (`x = f"...{ternary}..."`) -> merge_ctx == 'store'.
S3: S1 inside a try body whose handler adds an exception successor.
"""


class _Obj(object):
    order_id = 1
    symbol = 'x'
    entrust_direction = 0


class _ED(object):
    BUY = 0


class _Log(object):
    def info(self, msg):
        return msg


class _StratLog(object):
    def info(self, msg):
        return msg

    def error(self, msg):
        return msg


strategy_log = _StratLog()
_ = lambda s: s


def s1(order, amount):
    strategy_log.info(_(f"生成订单，订单号：{order.order_id!s} 代码：{order.symbol!s} 数量："
                        f"{'申购' if order.entrust_direction == _ED.BUY else '赎回'}{abs(amount)!s}"))


def s2(order, amount):
    msg = (f"生成订单，订单号：{order.order_id!s} 代码：{order.symbol!s} 数量："
           f"{'申购' if order.entrust_direction == _ED.BUY else '赎回'}{abs(amount)!s}")
    return msg


def s3(order, amount):
    try:
        strategy_log.info(_(f"生成订单，订单号：{order.order_id!s} 代码：{order.symbol!s} 数量："
                            f"{'申购' if order.entrust_direction == _ED.BUY else '赎回'}{abs(amount)!s}"))
        strategy_log.error('after')
    except Exception as e:
        strategy_log.error(f"err {e}")
