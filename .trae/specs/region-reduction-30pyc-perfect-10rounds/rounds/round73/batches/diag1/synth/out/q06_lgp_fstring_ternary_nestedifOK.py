# Source Generated with Decompyle++ (Python version)
# File: q06_lgp_fstring_ternary_nestedif.pyc (Python 3.11)

def q06(stocks, typet, is_utc, panel):
    log(f'n={len(stocks) if isinstance(stocks, list) else 1!s} t={typet!s}')
    panel = load_bars(stocks, typet)
    len(panel) != 0
    if len(panel) != 0 and is_utc == '0':
        panel = panel.tz_convert('Asia/Shanghai')
    return panel
def load_bars(stocks, typet):
    return stocks
