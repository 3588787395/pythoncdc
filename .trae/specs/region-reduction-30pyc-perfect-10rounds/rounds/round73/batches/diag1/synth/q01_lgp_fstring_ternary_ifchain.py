
# F-OTHER quote.load_get_price gap hunt q01: full mirror of the original shape
# (f-string ternary with !s conversion inside a CALL, then an assignment, then an
# outer `if len(x)!=0:` whose body is a nested if/elif chain).  Trigger sought:
# TernaryRegion claims the merge block which is ALSO the condition block of the
# following if -> the outer if degenerates to a bare expression statement.
def load_get_price(stocks, typet, is_utc, panel):
    log(f'params stocks={stocks[:10]!s} n={len(stocks) if isinstance(stocks, list) else 1!s} typet={typet!s}')
    panel = load_bars(stocks, typet)
    if len(panel) != 0:
        if is_utc == '0':
            if typet in (1, 2, 3, 4, 5, 13):
                panel = panel.tz_convert('Asia/Shanghai')
        elif typet in (1, 2, 3, 4, 5, 13):
            panel = panel.tz_localize('UTC').tz_convert('Asia/Shanghai')
    return panel


def load_bars(stocks, typet):
    return stocks
