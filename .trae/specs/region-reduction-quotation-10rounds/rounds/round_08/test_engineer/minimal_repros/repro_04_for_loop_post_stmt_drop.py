"""R8 repro_04: change_his_to_backward for 循环后语句丢失。
缺陷: for 循环体内及循环后语句被部分丢弃，导致 -57 指令差异。
区域类型: Loop  违反原则: 2(每块唯一归属)
"""
def f(security, data, exrights, start, end, typet):
    dates = list(data.index)
    for i in range(len(dates)):
        d = dates[i]
        if d in exrights:
            ex = exrights[d]
            if typet == 6:
                data.loc[d, 'open'] = data.loc[d, 'open'] * ex
                data.loc[d, 'close'] = data.loc[d, 'close'] * ex
            else:
                data.loc[d, 'open'] = data.loc[d, 'open'] / ex
        i = i + 1
    result = data.fillna(0)
    return result
