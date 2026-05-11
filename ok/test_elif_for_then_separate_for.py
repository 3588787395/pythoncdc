def func(stocks):
    result = {}
    if isinstance(stocks, str):
        stocks = [stocks]
    elif isinstance(stocks, list):
        for stock in stocks:
            result[stock] = True
    else:
        return result
    for stock in stocks:
        pass
    return result
