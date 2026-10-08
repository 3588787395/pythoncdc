# Source Generated with Decompyle++ (Python version)
# File: r10ls_08_deep_nest.pyc (Python 3.11)

def r10ls_08_deep_nest(order, asset, trading_date, gem_change_date, stock_listed_date_str, is_first_five_trading_days, deal_price):
    if cfg.on:
        for account, order in open_orders:
            if account.kind == 1:
                note(account)
                continue
            if order.asset.symbol[:3] == '300' and trading_date >= gem_change_date and stock_listed_date_str >= gem_change_date:
                if is_first_five_trading_days or order.entrust_direction == EntrustDirection.BUY and deal_price >= self._engine.data_cache.get_limit_up(asset.symbol):
                    continue
                elif order.entrust_direction == EntrustDirection.SELL and deal_price <= self._engine.data_cache.get_limit_down(asset.symbol):
                    continue
            if order.asset.symbol[:3] in ('688', '689'):
                if is_first_five_trading_days or order.entrust_direction == EntrustDirection.BUY and deal_price >= self._engine.data_cache.get_limit_up(asset.symbol):
                    continue
                elif order.entrust_direction == EntrustDirection.SELL and deal_price <= self._engine.data_cache.get_limit_down(asset.symbol):
                    continue
