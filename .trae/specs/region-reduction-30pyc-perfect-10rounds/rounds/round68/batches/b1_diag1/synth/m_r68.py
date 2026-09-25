# -*- coding: utf-8 -*-
"""Round 68 diag1 synthetic reproduction (R68-B/R68-C/R68-E over-absorption).

Trimmed copy of DefaultMatcher.match in
site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc.
Compiled with the local CPython 3.11.7 (magic 0xa70d, same as the target pyc).

Shape under test: inside the loop body an `if/elif/else` chain whose inner arms
all end in `continue`, followed by a *sibling* statement after the whole
`if order.type == LIMIT: ... else: ...` pair.  Every arm collection of the inner
chain therefore reaches the shared join block of the sibling statement, whose
predecessors also come from outside the arm (the LIMIT/else seam).  Without the
R68-B gate (external-pred pruning for collections that DO have a merge) the
sibling statement and everything after it are absorbed into the innermost arm,
so the decompile nests `if self._volume_limit: ...` inside the limit-down chain
and drops the `elif`/`else` structure -> bytecode mismatch.

  M0: the shape above (must FAIL on landed, PASS on the candidate arm).
  M1: control, a plain if/elif/else chain with no trailing sibling statement.
"""

_ = lambda s: s


class _Log(object):
    def warning(self, msg):
        return msg


class _Bus(object):
    def publish(self, *a, **k):
        return None


class _Bar(object):
    volume = 1


class _Engine(object):
    _price_limit = True
    _volume_limit = True
    _ratio = 1.0
    _turnover = {}
    _bus = _Bus()
    _log = _Log()
    _bars = {}
    _positions = {}

    def _price(self, symbol):
        return 1.0

    def _check(self, deal_price):
        return True

    def _up(self, symbol):
        return 10.0

    def _down(self, symbol):
        return 1.0

    def _next(self, d, n):
        return d

    def _fill(self, order, trade):
        return None


class _Asset(object):
    symbol = '600000'
    listed = '20240101'
    trade_unit = 100


class _Order(object):
    order_id = 1
    type = 1
    dir = 1
    price = 0.0
    amount = 10
    unfilled_amount = 10
    entrust_direction = 0
    asset = _Asset()
    mark_rejected = lambda self, r, **k: None
    mark_cancelled = lambda self, r, **k: None


def m0(engine, open_orders):
    for account, order in open_orders:
        asset = order.asset
        deal_price = engine._price(asset.symbol)
        if not engine._check(deal_price):
            reason = _('订单撤销: 已经退市 [{symbol}]').format(symbol=asset.symbol)
            order.mark_rejected(reason)
            engine._bus.publish(order)
            continue
        price = deal_price
        if order.type == 1:
            if order.dir == 1 and order.price < deal_price:
                continue
            elif order.dir == 2 and order.price > deal_price:
                continue
            else:
                if engine._price_limit:
                    trading_date = '20240101'
                    gem_change_date = '20240101'
                    stock_listed_date = asset.listed
                    stock_listed_date_str = stock_listed_date
                    if asset.symbol[:3] not in ('300', '688', '689'):
                        if order.dir == 1 and deal_price >= engine._up(asset.symbol):
                            continue
                        elif order.dir == 2 and deal_price <= engine._down(asset.symbol):
                            continue
                    elif asset.symbol[:3] == '300':
                        if not trading_date < gem_change_date:
                            if asset.symbol[:3] == '300' and stock_listed_date_str < gem_change_date:
                                if order.dir == 1 and deal_price >= engine._up(asset.symbol):
                                    continue
                                elif order.dir == 2 and deal_price <= engine._down(asset.symbol):
                                    continue
                                else:
                                    stock_listed_date = asset.listed
                                    next_trading_date = engine._next(stock_listed_date, 5)
                                    is_first = stock_listed_date <= trading_date <= next_trading_date
                                    if asset.symbol[:3] == '300' and trading_date >= gem_change_date and stock_listed_date_str >= gem_change_date:
                                        if is_first or order.dir == 1 and deal_price >= engine._up(asset.symbol):
                                            continue
                                        elif order.dir == 2 and deal_price <= engine._down(asset.symbol):
                                            continue
                                        elif asset.symbol[:3] in ('688', '689'):
                                            if is_first or order.dir == 1 and deal_price >= engine._up(asset.symbol):
                                                continue
                                            elif order.dir == 2 and deal_price <= engine._down(asset.symbol):
                                                continue
        else:
            if engine._price_limit:
                if order.dir == 1 and deal_price >= engine._up(asset.symbol):
                    order.mark_rejected(_('订单撤销: 撮合价格超涨停价'))
                    engine._bus.publish(order)
                    continue
                if order.dir == 2 and deal_price <= engine._down(asset.symbol):
                    order.mark_rejected(_('订单撤销: 撮合价格超跌停价'))
                    engine._bus.publish(order)
                    continue
        if engine._volume_limit:
            bar = engine._bars.get(asset.symbol) or _Bar()
            if bar.volume == 0:
                order.mark_cancelled(_('订单撤销: bar.volume {bar_volume}').format(symbol=asset.symbol, bar_volume=bar.volume))
                continue
            volume_limit = round(bar.volume * engine._ratio) - engine._turnover.get(asset.symbol, 0)
            volume_limit = volume_limit // asset.trade_unit * asset.trade_unit
            if volume_limit <= 0:
                if order.type == 9:
                    order.mark_cancelled(_('订单撤销: volume {order_volume}').format(symbol=asset.symbol, volume=order.amount))
                continue
            fill = min(order.unfilled_amount, volume_limit)
            if fill < order.amount:
                engine._log.warning('over fill {fill}'.format(fill=fill))
        else:
            fill = order.unfilled_amount
        position = engine._positions.get(asset.symbol)
        trade = ('T', order.order_id, price, fill, position, order.entrust_direction)
        engine._fill(order, trade)
        engine._turnover[asset.symbol] = engine._turnover.get(asset.symbol, 0) + fill
        if order.unfilled_amount != 0:
            order.mark_cancelled(_('Order Cancelled {symbol}').format(symbol=asset.symbol))
            engine._bus.publish(order)


def m1(order, engine):
    if order.type == 1:
        if order.dir == 1 and order.price < 1:
            return 'buy-low'
        elif order.dir == 2 and order.price > 1:
            return 'sell-high'
        else:
            if engine._price_limit:
                return 'limit'
    else:
        if engine._price_limit:
            if order.dir == 1:
                return 'up'
            elif order.dir == 2:
                return 'down'
    return 'tail'
