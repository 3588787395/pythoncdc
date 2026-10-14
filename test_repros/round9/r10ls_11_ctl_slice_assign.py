def r10ls_11_ctl_slice_assign(order, asset, trading_date, gem_change_date, stock_listed_date_str, is_first_five_trading_days, deal_price):
    for account, order in open_orders:
        prefix = order.asset.symbol[:3]
        if prefix in ('688', '689'):
            flag = True
