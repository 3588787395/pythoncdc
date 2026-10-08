def r10ls_14_ctl_nonslice_pair(order, asset, trading_date, gem_change_date, stock_listed_date_str, is_first_five_trading_days, deal_price):
    for account, order in open_orders:
        if account.kind == 1:
            note(account)
        else:
            if order.asset.symbol == '300' and trading_date >= gem_change_date and stock_listed_date_str >= gem_change_date and not is_first_five_trading_days:
                if order.entrust_direction == EntrustDirection.BUY and deal_price >= self._engine.data_cache.get_limit_up(asset.symbol):
                    continue
                elif order.entrust_direction == EntrustDirection.SELL and deal_price <= self._engine.data_cache.get_limit_down(asset.symbol):
                    continue
            if order.asset.symbol in ('688', '689') and not is_first_five_trading_days:
                if order.entrust_direction == EntrustDirection.BUY and deal_price >= self._engine.data_cache.get_limit_up(asset.symbol):
                    continue
                elif order.entrust_direction == EntrustDirection.SELL and deal_price <= self._engine.data_cache.get_limit_down(asset.symbol):
                    continue
