"""R8 repro_01: one_prod_to_dataframe elif 链条件污染。
缺陷: 外层 `if i == 0:` 的条件被错误附加到内层 elif 条件上 (`elif i == 0 and len(v)==10`)，
且部分 elif 的 `len(v)==N` 比较被丢弃变为裸 `elif i == 0:`，导致 +10 指令差异。
区域类型: Conditional + BoolOp  违反原则: 2(每块唯一归属) + 4(入口引用语义)
"""
def f(fields, prod):
    index = []
    i = 0
    for v in prod:
        if i == 0:
            if len(v) == 8:
                index.append(v)
            elif len(v) == 10:
                index.append(v)
            elif len(v) == 9:
                index.append(v)
            elif len(v) == 12:
                index.append(v)
            elif len(v) == 14:
                index.append(v)
        i = i + 1
    return index
