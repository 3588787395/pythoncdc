"""repro_09: get_str_data first_diff@9 (外层 FOR_ITER 目标偏移)
区域类型: Loop (outer for items)
违反原则: 4 (入口引用语义)
对应函数: get_str_data (first_diff_idx=9, 外层 for stock, stock_df in rdata.items())
缺陷镜像: 外层 `for stock, stock_df in rdata.items():` 的 FOR_ITER 跳转目标
  orig ->[305] vs new ->[257]，差异源于内层循环体 -48 指令丢失导致整体偏移。
  根因不在外层 for 本身，而在内层 LoopRegion@610 的 TernaryRegion 兄弟被误吞。
  此 repro 验证外层 for + 内层 for + 内层 if(continue) 的最小组合。
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
