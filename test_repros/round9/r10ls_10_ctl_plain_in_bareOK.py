# Source Generated with Decompyle++ (Python version)
# File: r10ls_10_ctl_plain_in_bare.pyc (Python 3.11)

def r10ls_10_ctl_plain_in_bare(order, asset, trading_date, gem_change_date, stock_listed_date_str, is_first_five_trading_days, deal_price):
    for account, order in open_orders:
        if order.asset.symbol in ('688', '689'):
            flag = True
