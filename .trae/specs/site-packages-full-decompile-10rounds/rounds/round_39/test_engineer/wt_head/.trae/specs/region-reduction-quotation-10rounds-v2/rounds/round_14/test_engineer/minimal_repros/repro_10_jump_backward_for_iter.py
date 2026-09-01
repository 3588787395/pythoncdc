"""复现 10：for 循环 JUMP_BACKWARD 跳回 FOR_ITER 的归一化。

模式：for 循环体末尾 JUMP_BACKWARD 跳回 FOR_ITER 指令。
JUMP_BACKWARD 的 argval 是字节码 offset，需归一化为指令索引。
当 orig/new 指令布局有 2 字节偏移时，offset 不同但指令索引相同。

对应函数：one_prod_to_dataframe @idx427
"""
def f(data):
    cols = ['open', 'close', 'high', 'low']
    result = {}
    for c in cols:
        result[c] = []
        for row in data:
            if c in row:
                result[c].append(row[c])
    return result
