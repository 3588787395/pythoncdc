# Source Generated with Decompyle++ (Python version)
# File: r10ls_04_finally_ctx.pyc (Python 3.11)

def r10ls_04_finally_ctx(order, asset, trading_date, gem_change_date, stock_listed_date_str, is_first_five_trading_days, deal_price):
    for account, order in open_orders:
        try:
            note(account)
        finally:
            if order.asset.symbol[:3] == '300':
                pass
            elif order.asset.symbol[:3] in ('688', '689'):
                pass
            if order.entrust_direction == EntrustDirection.BUY and deal_price >= self._engine.data_cache.get_limit_up(asset.symbol):
                pass
            elif order.entrust_direction == EntrustDirection.SELL and deal_price <= self._engine.data_cache.get_limit_down(asset.symbol):
                pass
            if stock_listed_date_str >= gem_change_date:
                pass
            if order.entrust_direction == EntrustDirection.BUY and deal_price >= self._engine.data_cache.get_limit_up(asset.symbol):
                pass
            elif order.entrust_direction == EntrustDirection.SELL and deal_price <= self._engine.data_cache.get_limit_down(asset.symbol):
                pass
