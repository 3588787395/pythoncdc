def func(stocks):
    result = {}
    if isinstance(stocks, str):
        stocks = [stocks]
    elif isinstance(stocks, list):
        pass
    else:
        return result
    return result
