# R5 minimal repro: elif 分支内语句重复 + 裸 Name + spurious for-else
# 关联缺陷：quotation.pyc load_get_index_stocks line 789-796 / load_get_industry_stocks line 803-810 (新发现)
# 触发区域：IF / _generate_if + _generate_loop (elif 分支内 stockslist=[] 重复, 裸 stocks Name, 末尾顺序语句误并入 for-else)
# 预期：elif isinstance(stocks, list): stockslist=[]; for s in stocks: stockslist.extend(f(s))
#                                       data = list(set(stockslist)); return data.sort(key=stockslist.index)
# R5 实际产物：
#   elif isinstance(stocks, list):
#       stockslist = []
#       stocks                          <- 裸 Name
#       stockslist = []                 <- 重复
#       for s in stocks: stockslist.extend(f(s))
#       else:                           <- spurious for-else
#           data = list(set(stockslist))
#           return data.sort(key=stockslist.index)


def load_get_index_stocks(stocks):
    data = []
    if isinstance(stocks, str):
        data = get_local(stocks)
    elif isinstance(stocks, list):
        stockslist = []
        for s in stocks:
            stockslist.extend(get_local(s))
        data = list(set(stockslist))
        return data.sort(key=stockslist.index)
    return data
