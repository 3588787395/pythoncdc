def func(stocks):
    result = {}
    if isinstance(stocks, str):
        stocks = [stocks]
    elif isinstance(stocks, list):
        for stock in stocks:
            pass
    else:
        return result
    return result
