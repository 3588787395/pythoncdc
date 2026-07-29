"""复现 01：if/elif 链第一个条件短路跳转目标归一化。

模式：`if i==0 and cond:` 的 `i==0` 短路跳转，orig 跳到下一 elif 分支入口，
new 跳到整个 if/elif 链末尾。语义等价（后续分支均以 i==0 为前提条件）。

对应函数：one_prod_to_dataframe @idx131
"""
def f(v, i):
    index = []
    if i == 0 and len(v) == 8:
        index.append(v[0:4])
    elif i == 0 and len(v) == 10:
        index.append(v[0:4])
    elif i == 0 and len(v) == 12:
        index.append(v[0:4])
    i = i + 1
    return index
