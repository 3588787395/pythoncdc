# Source Generated with Decompyle++ (Python version)
# File: price_validator.pyc (Python 3.11)

import datetime
from IQEngine.interface import AbstractFrontendValidator
from IQEngine.const import OrderType
from IQEngine.utils import user_log
class PriceValidator(AbstractFrontendValidator):
    def __init__(self, engine):
        self._engine = engine
    def can_submit_order(self, account, order):
        trading_date = self._engine.trading_dt.strftime('%Y%m%d')
        gem_change_date = str(self._engine.config.plugins.plugin_system_risk_control.gem_change_date)
        stock_listed_date = order.asset.listed_date
        stock_listed_date_str = stock_listed_date.strftime('%Y%m%d')
        if order.asset.symbol[:3] == '300' and trading_date >= gem_change_date and stock_listed_date_str >= gem_change_date:
            next_trading_date = self._engine.data_proxy.get_next_trading_date(stock_listed_date, 5)
            is_first_five_trading_days = stock_listed_date <= self._engine.trading_dt <= next_trading_date
            if is_first_five_trading_days:
                return True
        if order.asset.symbol[:3] in ('688', '689') and trading_date >= stock_listed_date_str:
            next_trading_date = self._engine.data_proxy.get_next_trading_date(stock_listed_date, 5)
            is_first_five_trading_days = stock_listed_date <= self._engine.trading_dt <= next_trading_date
            if is_first_five_trading_days:
                return True
        if order.type == OrderType.LIMIT.value:
            price = order.price
        else:
            deal_price = self._engine.get_last_price(order.symbol)
            price = self._engine.slippage.calculate_trade_price(order, deal_price)
        limit_up = self._engine.data_cache.get_limit_up(order.asset.symbol)
        limit_down = self._engine.data_cache.get_limit_down(order.asset.symbol)
        if limit_down <= price <= limit_up:
            return True
        else:
            user_log.warning('{symbol}下单价格超涨跌幅范围[{limit_down},{limit_up}]，下单失败'.format(symbol=order.symbol, limit_down=limit_down, limit_up=limit_up))
            return False
    def can_cancel_order(self, account, order):
        return True
