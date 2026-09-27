# Source Generated with Decompyle++ (Python version)
# File: q01_lgp_fstring_ternary_ifchain.pyc (Python 3.11)

def load_get_price(stocks, typet, is_utc, panel):
    log(f'params stocks={stocks[:10]!s} n={len(stocks) if isinstance(stocks, list) else 1!s} typet={typet!s}')
    panel = load_bars(stocks, typet)
    len(panel) != 0
    if is_utc == '0':
        if typet in (1, 2, 3, 4, 5, 13):
            panel = panel.tz_convert('Asia/Shanghai')
    elif typet in (1, 2, 3, 4, 5, 13):
        panel = panel.tz_localize('UTC').tz_convert('Asia/Shanghai')
    return panel
def load_bars(stocks, typet):
    return stocks
