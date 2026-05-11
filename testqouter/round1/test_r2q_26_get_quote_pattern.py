def test():
    quote = None
    log, is_trade = False, False
    if quote is None:
        log, is_trade = True, False
        quote = 1 if is_trade else 0
    return quote
