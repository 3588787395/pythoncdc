# R5 minimal repro: else 块后顺序语句被复制进 else + 重复 + spurious for-else (R4 残留 #6 同源)
# 关联缺陷：quotation.pyc change_his_to_forward line 628-635  tmpstartindex 未赋值即使用 (R4 残留 #6)
# 触发区域：IF / _generate_if + _generate_region (else 块后顺序语句被误并入 else 并重复, 末尾 for 误加 else)
# 预期：else: preindex=None; tmpdata=None
#       tmpstartindex = series[:start].index[-1]      <- else 后顺序语句
#       tmpendindex = series[end:].index[0]
#       for n in list(...): tmpdata = data[preindex:n]
# R5 实际产物：
#   else: preindex=None; tmpdata=None; tmpstartindex=...; tmpendindex=...; list(...)  <- 顺序语句被复制进 else, list(...) 裸 Expr
#   preindex=None; tmpdata=None; tmpstartindex=...; tmpendindex=...                   <- 重复
#   for n in list(...): tmpdata = data[preindex:n]
#   else: return tmpdata                                                                <- spurious for-else


def change_his_to_forward(security, data, exrights_data, start, end, typet):
    if len(data) == 0:
        return data
    else:
        firstdate = list(data.index)[0]
        if start != firstdate:
            start = firstdate
        fields = ['open', 'close', 'high', 'low', 'price']
        series = exrights_data[security]
        if series.empty:
            return data
        elif series[start:].empty:
            return data
        else:
            preindex = None
            tmpdata = None
        tmpstartindex = series[:start].index[-1]
        tmpendindex = series[end:].index[0]
        for n in list(series[tmpstartindex:tmpendindex].index):
            tmpdata = data[preindex:n]
        return tmpdata
