"""R9 repro_04: get_str_data 嵌套 for+while 循环体语句丢失(-48)。
缺陷: 外层 for 循环体内赋值 + 内层 while 循环体 if/else 分支语句部分丢失。
区域类型: Loop  违反原则: 2(每块唯一归属)
"""
def f(rdata):
    order_data = {}
    for stock in rdata:
        stock_df = rdata[stock]
        dates = list(stock_df.index)
        n = len(stock_df)
        datass_list = []
        datas_index = []
        i = 0
        j = 0
        while j < n:
            if dates[i] == dates[j]:
                datas_index.append(j)
                i = j
                j = j + 1
            else:
                datass_list.append(datas_index)
                datas_index = []
                i = j
                j = j + 1
        order_data[stock] = datass_list
    return order_data
