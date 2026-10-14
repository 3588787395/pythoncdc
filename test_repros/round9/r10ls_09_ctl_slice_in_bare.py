def r10ls_09_ctl_slice_in_bare(order, asset, trading_date, gem_change_date, stock_listed_date_str, is_first_five_trading_days, deal_price):
    for account, order in open_orders:
        if order.asset.symbol[:3] in ('688', '689'):
            flag = True
