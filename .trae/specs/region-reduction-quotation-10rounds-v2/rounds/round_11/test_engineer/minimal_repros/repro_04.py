"""repro_04: get_str_data 嵌套 for 循环体语句丢失 (-48)
区域类型: Loop
违反原则: 2 (每块唯一归属)
对应函数: get_str_data
缺陷镜像: 外层 `for stock, stock_df in rdata.items():` 内嵌 `for i in datetime_index: dates.append(i)`，
  _generate_loop 遍历循环体块时漏掉 merge/follow 块，内层循环体与后续 `order_data[stock]=dates` 丢失。
  diff_detail first_diff_idx=9 (外层 FOR_ITER 处即开始发散)。
"""


def f(rdata):
    order_data = {}
    for stock, stock_df in rdata.items():
        datetime_index = stock_df.index
        dates = []
        for i in datetime_index:
            dates.append(i)
        order_data[stock] = dates
    return order_data
