
# q06: f-string ternary + assignment + outer if whose body is a single nested if
def q06(stocks, typet, is_utc, panel):
    log(f'n={len(stocks) if isinstance(stocks, list) else 1!s} t={typet!s}')
    panel = load_bars(stocks, typet)
    if len(panel) != 0:
        if is_utc == '0':
            panel = panel.tz_convert('Asia/Shanghai')
    return panel


def load_bars(stocks, typet):
    return stocks
