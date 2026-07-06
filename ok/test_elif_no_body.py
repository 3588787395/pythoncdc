"""测试elif没有body的情况（与quote.pyc中的问题类似）"""

def func(stocks):
    result = {}
    if isinstance(stocks, str):
        stocks = [stocks]
    elif isinstance(stocks, list):
        # 这里没有任何语句
        pass
    else:
        return result
    return result
