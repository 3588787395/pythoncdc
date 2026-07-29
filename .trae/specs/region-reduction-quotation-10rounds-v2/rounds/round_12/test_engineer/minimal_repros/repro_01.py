"""repro_01: get_str_data 嵌套 for 循环体 + IfRegion(continue) + 兄弟 TernaryRegion 丢失 (-48)
区域类型: Loop + IfRegion(continue) + TernaryRegion
违反原则: 3 (嵌套即抽象节点) + 4 (入口引用语义)
对应函数: get_str_data
缺陷镜像: 外层 `for stock, stock_df in rdata.items():` 内嵌 `for datas in datass_list:`，
  内层 for 体含 `if datas: continue`（IfRegion merge=loop header），
  IfRegion.else_blocks 包含后续 TernaryRegion@844/@1226 的 entry。
  _if_generate_else_branch 不分发 TernaryRegion/BoolOpRegion（不同于 then 分支），
  导致 TernaryRegion 块被 _process_if_blocks 平坦化为顺序块并标记 generated，
  后续父循环遍历跳过 TernaryRegion，-48 指令丢失。
  diff_detail first_diff_idx=9 (外层 FOR_ITER 处即开始发散)。
"""


def f(rdata):
    order_data = {}
    for stock, stock_df in rdata.items():
        datetime_index = stock_df.index
        dates = []
        for i in datetime_index:
            dates.append(i)
        n = len(stock_df.iloc[:, 0])
        datass_list = []
        i = 0
        j = 0
        while j < n:
            if _is_same_type_date(dates, i, j, 0):
                datass_list.append([j])
                i = j
            j += 1
        data = {}
        time_index = []
        count = 0 if not count else count
        for datas in datass_list[count:]:
            if not datas:
                continue
            is_all_nan = _check_nan(stock_df, datas, 'open')
            not_nan_icount = 0
            for j in range(len(is_all_nan)):
                if is_all_nan[j] == True and j == len(is_all_nan) - 1:
                    data_is_nan = 1
            price = stock_df.ix[datas[not_nan_icount]]['open'] if data_is_nan == 1 else stock_df.ix[datas[-1]]['price']
            data[i] = {'open': 0, 'close': 0, 'high': 0, 'low': 0, 'volume': 0, 'price': price, 'money': 0}
            time_index.append(datas)
        order_data[stock] = data
    return order_data


def _is_same_type_date(dates, i, j, typet):
    return True


def _check_nan(stock_df, datas, key):
    return [False]
