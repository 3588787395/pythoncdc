def test():
    quote = None
    if quote is None:
        log, is_trade = (True, False)
        quote = 'trade' if is_trade else 'backtest'
    return quote
