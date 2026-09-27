
# q02: f-string ternary + assignment + SIMPLE outer if (no nested chain)
def q02(stocks, typet, panel):
    log(f'n={len(stocks) if isinstance(stocks, list) else 1!s} t={typet!s}')
    panel = load_bars(stocks, typet)
    if len(panel) != 0:
        panel = panel.dropna()
    return panel


def load_bars(stocks, typet):
    return stocks
