# Source Generated with Decompyle++ (Python version)
# File: q02_lgp_fstring_ternary_simpleif.pyc (Python 3.11)

def q02(stocks, typet, panel):
    log(f'n={len(stocks) if isinstance(stocks, list) else 1!s} t={typet!s}')
    panel = load_bars(stocks, typet)
    len(panel) != 0
    panel = panel.dropna()
    return panel
def load_bars(stocks, typet):
    return stocks
