def func(stocks):
    result = {}
    for stock in stocks:
        result[stock] = True
    else:
        if isinstance(stocks, str):
            stocks = [stocks]
    return result
