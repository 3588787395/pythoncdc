"""R8 repro_03: get_str_data 嵌套 for 循环后构造丢失。
缺陷: 外层 for 循环体内的语句及循环后构造语句被部分丢弃，导致 -48 指令差异。
区域类型: Loop  违反原则: 2(每块唯一归属)
"""
def f(rdata, count, typet):
    order_data = {}
    for stock in rdata:
        stock_df = rdata[stock]
        dates = []
        for i in stock_df:
            dates.append(i)
        n = len(stock_df)
        datass_list = []
        datas_index = []
        j = 0
        while j < n:
            if dates[i] == dates[j]:
                datas_index.append(j)
                i = j
                j += 1
            else:
                datass_list.append(datas_index)
                datas_index = []
                i = j
                j += 1
        order_data[stock] = datass_list
    return order_data
