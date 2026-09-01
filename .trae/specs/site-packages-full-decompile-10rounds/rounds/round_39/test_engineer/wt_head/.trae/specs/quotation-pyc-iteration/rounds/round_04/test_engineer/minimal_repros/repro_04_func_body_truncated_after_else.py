# R4 minimal repro: 函数体在 elif/else 链 + 复杂 for 循环后整段截断
# 关联缺陷：新发现 (R4 新增, change_his_to_forward R3=239 -> R4=181 回归)
# 触发区域：IF + LOOP
# 预期：完整 elif 链 + else 分支后的 for 循环 + 复杂赋值
# R4 实际产物：else: tmpdata = None 后整段截断 (丢失 tmpstartindex/tmpendindex/tmp 变量)
def change_his_to_forward(security, data, exrights_data, start, end, typet):
    if len(data) == 0:
        return data
    firstdate = list(data.index)[0].tz_localize(None).to_pydatetime().strftime('%Y%m%d')
    if start != firstdate:
        start = firstdate
    if len(start) > 8:
        start = start[:8]
    if len(end) > 8:
        end = end[:8]
    startDateIndex = datetime.strptime(start, '%Y%m%d').strftime('%Y-%m-%d 00:00:00')
    endDateIndex = datetime.strptime(end, '%Y%m%d').strftime('%Y-%m-%d 00:00:00')
    fields = ['open', 'close', 'high', 'low', 'price']
    if typet == 6:
        fields = ['open', 'close', 'high', 'low', 'price', 'preclose', 'high_limit', 'low_limit']
    series = exrights_data[security]
    if series.empty:
        return data
    elif series[startDateIndex:].empty:
        return data
    elif startDateIndex == endDateIndex and n == startDateIndex:
        if len(series[startDateIndex:].index) > 1:
            n = list(series[startDateIndex:].index)[1]
            data = data * float(series.loc[n, 'exer_forward_a']) + float(series.loc[n, 'exer_forward_b'])
            return round(data, 2)
        else:
            return data
    else:
        preindex = None
        tmpdata = None
        tmpstartindex = None
        tmpendindex = None
        tmp = None
        for idx in series[startDateIndex:endDateIndex].index:
            if preindex is None:
                preindex = idx
                tmpstartindex = idx
            else:
                tmpendindex = idx
                tmp = series.loc[idx, 'exer_forward_a']
                tmpdata = data * float(tmp)
        if tmpdata is not None:
            data = tmpdata
            return round(data, 2)
        return data
