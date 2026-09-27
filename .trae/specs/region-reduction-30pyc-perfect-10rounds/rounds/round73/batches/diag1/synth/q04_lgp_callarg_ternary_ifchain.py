
# q04: ternary as plain call argument (no f-string) + assignment + if/elif chain
def q04(stocks, typet, is_utc, panel):
    log(len(stocks) if isinstance(stocks, list) else 1)
    panel = load_bars(stocks, typet)
    if len(panel) != 0:
        if is_utc == '0':
            panel = panel.tz_convert('Asia/Shanghai')
        elif typet in (1, 2, 3):
            panel = panel.tz_convert('UTC')
    return panel


def load_bars(stocks, typet):
    return stocks
