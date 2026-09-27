
# q05: assigned ternary + assignment + if/elif chain (value-context control)
def q05(stocks, typet, is_utc, panel):
    n = len(stocks) if isinstance(stocks, list) else 1
    panel = load_bars(stocks, typet)
    if n != 0:
        if is_utc == '0':
            panel = panel.tz_convert('Asia/Shanghai')
        elif typet in (1, 2, 3):
            panel = panel.tz_convert('UTC')
    return panel


def load_bars(stocks, typet):
    return stocks
