"""测试elif中包含self赋值的情况"""

def func(stocks):
    result = {}
    if isinstance(stocks, str):
        stocks = [stocks]
    elif isinstance(stocks, list):
        stocks = stocks  # self assignment
    else:
        return result
    return result
