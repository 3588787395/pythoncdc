"""复现 06：循环内嵌套 if/elif 链的短路跳转归一化。

模式：for 循环内部有 if/elif 链，第一个条件短路跳到下一分支 vs 链末尾（循环末尾 i+=1）。

对应函数：one_prod_to_dataframe（for 循环内 if/elif 链）
"""
def f(rows):
    index = []
    i = 0
    for v in rows:
        if i == 0 and len(v) == 8:
            index.append(v[0:4])
        elif i == 0 and len(v) == 10:
            index.append(v[0:4])
        elif i == 0 and len(v) == 12:
            index.append(v[0:4])
        i = i + 1
    return index
