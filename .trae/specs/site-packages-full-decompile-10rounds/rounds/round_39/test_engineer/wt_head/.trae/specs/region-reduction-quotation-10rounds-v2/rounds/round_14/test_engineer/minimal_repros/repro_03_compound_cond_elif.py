"""复现 03：复合条件 and 短路的 elif 链。

模式：`if a and b:` 中 a 短路跳到下一分支入口 vs 链末尾。
当所有 elif 分支都以 a 为第一条件时，a 为假则整链跳过，语义等价。

对应函数：one_prod_to_dataframe @idx131 (i==0 and len(v)==8)
"""
def f(v, i):
    out = []
    if i == 0 and len(v) == 8:
        out.append(v)
    elif i == 0 and len(v) == 10:
        out.append(v)
    elif i == 0 and len(v) == 12:
        out.append(v)
    elif i == 0 and len(v) == 14:
        out.append(v)
    return out
