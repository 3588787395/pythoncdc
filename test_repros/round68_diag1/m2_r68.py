# -*- coding: utf-8 -*-
"""Round 68 diag1 synthetic witness (R68-B / R68-C / R68-E over-absorption).

Trimmed copy of DefaultMatcher.match in
site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc; only the
match() method is kept, every module-level import is replaced by a stub.
Compiled with the local CPython 3.11.7 (magic 0xa70d, same as the target pyc).

Failure signature: on landed this reproduces matcher::match 16/17 with
mism [715, 715, 10, 517] (the limit-chain else arm absorbs the trailing
sibling block); on the candidate arm it is 17/17.
"""
from enum import IntEnum


class MatcherType(IntEnum):
    CURRENT_BAR_CLOSE = 1
    CURRENT_BAR_OPEN = 2
    CURRENT_BAR_HIGH = 3
    CURRENT_BAR_LOW = 4


class LimitMode(IntEnum):
    LIMIT = 1
    MARKET = 2


class EntrustDirection(IntEnum):
    BUY = 1
    SELL = 2


class OrderType(IntEnum):
    LIMIT = 1
    MARKET = 2


def check_price(p):
    return True


class Trade(object):
    @staticmethod
    def create_trade(**kw):
        return kw


class Event(object):
    def __init__(self, *a, **k):
        pass


class EventEnum(object):
    ORDER_TRADE = 1
    ON_TRADE_RSP = 2


_ = lambda s: s


class _Log(object):
    def warning(self, *a, **k):
        return None


strategy_log = _Log()


class AbstractMatcher(object):
    def __init__(self, engine=None):
        self._engine = engine


class DefaultMatcher(AbstractMatcher):
    __doc__ = """
    模拟撮合类
    
    此对象负责对订单进行撮合
    """
    CURRENT_BAR_MATCH = [MatcherType.CURRENT_BAR_CLOSE, MatcherType.CURRENT_BAR_OPEN, MatcherType.CURRENT_BAR_HIGH, MatcherType.CURRENT_BAR_LOW]

    def match(self, open_orders):
        for account, order in open_orders:
            asset = order.asset
            deal_price = self._deal_price_adapter(asset.symbol)
            if not check_price(deal_price):
                delisted_date = asset.delisted_date.date()
                if delisted_date == self._trading_dt.date():
                    reason = _('订单撤销: 当前合约 [{symbol}] 已经退市，无法进行交易，退市日期 [{delisted_date}]').format(symbol=asset.symbol, delisted_date=delisted_date)
                else:
                    reason = _('订单撤销: 获取当前周期的数据失败 [{symbol}]').format(symbol=asset.symbol)
                order.mark_rejected(reason)
                self._engine.event_bus.publish_event(Event(EventEnum.ON_TRADE_RSP, trade=order, order=order))
                continue
            price = self._engine.slippage.calculate_trade_price(order, deal_price)
            if order.type == OrderType.LIMIT.value:
                if order.entrust_direction == EntrustDirection.BUY and order.price < deal_price:
                    continue
                elif order.entrust_direction == EntrustDirection.SELL and order.price > deal_price:
                    continue
                else:
                    if self._price_limit:
                        trading_date = self._engine.trading_dt.strftime('%Y%m%d')
                        gem_change_date = str(self._engine.config.plugins.plugin_system_risk_control.gem_change_date)
                        stock_listed_date = order.asset.listed_date
                        stock_listed_date_str = stock_listed_date.strftime('%Y%m%d')
                        if order.asset.symbol[:3] not in ('300', '688', '689'):
                            if order.entrust_direction == EntrustDirection.BUY and deal_price >= self._engine.data_cache.get_limit_up(asset.symbol):
                                continue
                            elif order.entrust_direction == EntrustDirection.SELL and deal_price <= self._engine.data_cache.get_limit_down(asset.symbol):
                                continue
                        elif order.asset.symbol[:3] == '300':
                            if not trading_date < gem_change_date:
                                if order.asset.symbol[:3] == '300' and stock_listed_date_str < gem_change_date:
                                    if order.entrust_direction == EntrustDirection.BUY and deal_price >= self._engine.data_cache.get_limit_up(asset.symbol):
                                        continue
                                    elif order.entrust_direction == EntrustDirection.SELL and deal_price <= self._engine.data_cache.get_limit_down(asset.symbol):
                                        continue
                                    else:
                                        stock_listed_date = order.asset.listed_date
                                        next_trading_date = self._engine.data_proxy.get_next_trading_date(stock_listed_date, 5)
                                        is_first_five_trading_days = stock_listed_date <= self._engine.trading_dt <= next_trading_date
                                        if order.asset.symbol[:3] == '300' and trading_date >= gem_change_date and stock_listed_date_str >= gem_change_date:
                                            if is_first_five_trading_days or order.entrust_direction == EntrustDirection.BUY and deal_price >= self._engine.data_cache.get_limit_up(asset.symbol):
                                                continue
                                            elif order.entrust_direction == EntrustDirection.SELL and deal_price <= self._engine.data_cache.get_limit_down(asset.symbol):
                                                continue
                                            elif order.asset.symbol[:3] in ('688', '689'):
                                                if is_first_five_trading_days or order.entrust_direction == EntrustDirection.BUY and deal_price >= self._engine.data_cache.get_limit_up(asset.symbol):
                                                    continue
                                                elif order.entrust_direction == EntrustDirection.SELL and deal_price <= self._engine.data_cache.get_limit_down(asset.symbol):
                                                    continue
            else:
                if self._price_limit:
                    if order.entrust_direction == EntrustDirection.BUY and deal_price >= self._engine.data_cache.get_limit_up(asset.symbol):
                        reason = _('订单撤销: [{symbol}]撮合价格超涨停价').format(symbol=asset.symbol)
                        order.mark_rejected(reason)
                        self._engine.event_bus.publish_event(Event(EventEnum.ON_TRADE_RSP, trade=order, order=order))
                        continue
                    if order.entrust_direction == EntrustDirection.SELL and deal_price <= self._engine.data_cache.get_limit_down(asset.symbol):
                        reason = _('订单撤销: [{symbol}]撮合价格超跌停价').format(symbol=asset.symbol)
                        order.mark_rejected(reason)
                        self._engine.event_bus.publish_event(Event(EventEnum.ON_TRADE_RSP, trade=order, order=order))
                        continue
                    while False:
                        pass
            if self._volume_limit:
                bar = self._engine.bar_dict[asset.symbol]
                if bar.volume == 0:
                    reason = _('订单撤销:  当前bar交易量不足  {symbol}  bar.volume {bar_volume}').format(symbol=asset.symbol, bar_volume=bar.volume)
                    order.mark_cancelled(reason)
                    continue
                volume_limit = round(bar.volume * self._volume_ratio) - self._turnover[asset.symbol]
                volume_limit = volume_limit // asset.trade_unit * asset.trade_unit
                if volume_limit <= 0:
                    if order.type == OrderType.MARKET.value:
                        reason = _('订单撤销: 当前bar交易量不足 {symbol} volume {order_volume}').format(symbol=asset.symbol, order_volume=order.amount)
                        order.mark_cancelled(reason)
                    continue
                fill = min(order.unfilled_amount, volume_limit)
                if fill < order.amount:
                    strategy_log.warning(f'后端服务 当前策略成交比例设置为：{self._engine.matcher.get_volume_ratio()!s}，委托数量{order.amount!s}超过当前周期可成交数量，撮合成交数量调整为{fill!s}')
            else:
                fill = order.unfilled_amount
            position = account.positions.get_or_create(asset.symbol)
            trade = Trade.create_trade(order_id=order.order_id, price=price, amount=fill, entrust_direction=order.entrust_direction, futures_direction=order.futures_direction, hedge_type=order.hedge_type, asset=asset, frozen_price=order.frozen_price, close_today_amount=position.cal_close_today_amount(fill, order.entrust_direction))
            trade._commission = self._engine.commission.calculate_commission(trade)
            trade._tax = self._engine.commission.calculate_tax(trade)
            order.fill(trade)
            self._turnover[asset.symbol] += fill
            self._engine.event_bus.publish_event(Event(EventEnum.ORDER_TRADE, account=account, trade=trade, order=order))
            self._engine.event_bus.publish_event(Event(EventEnum.ON_TRADE_RSP, trade=trade, order=order))
            if order.unfilled_amount != 0:
                reason = _('Order Cancelled: market order {symbol} volume {order_volume} is larger than {volume_percent_limit} percent of current bar volume, fill {filled_volume} actually').format(symbol=asset.symbol, order_volume=order.amount, filled_volume=order.filled_amount, volume_percent_limit=self._volume_ratio * 100.0)
                order.mark_cancelled(reason, user_warn=False)
                self._engine.event_bus.publish_event(Event(EventEnum.ON_TRADE_RSP, trade=order, order=order))

