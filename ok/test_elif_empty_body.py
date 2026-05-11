"""测试elif空body的情况"""

def func(stocks):
    result = {}
    if isinstance(stocks, str):
        stocks = [stocks]
    elif isinstance(stocks, list):
        pass  # elif body为空
    else:
        return result
    return result
