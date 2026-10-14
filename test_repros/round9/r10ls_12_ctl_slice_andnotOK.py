# Source Generated with Decompyle++ (Python version)
# File: r10ls_12_ctl_slice_andnot.pyc (Python 3.11)

def r10ls_12_ctl_slice_andnot(order, asset, trading_date, gem_change_date, stock_listed_date_str, is_first_five_trading_days, deal_price):
    for account, order in open_orders:
        if order.asset.symbol[:3] in ('688', '689') and not is_first_five_trading_days:
            note(order)
