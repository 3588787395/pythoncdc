
# q03: f-string ternary + outer if directly (no intervening statement)
def q03(stocks, panel):
    log(f'n={len(stocks) if isinstance(stocks, list) else 1!s}')
    if len(panel) != 0:
        panel = panel.dropna()
    return panel
