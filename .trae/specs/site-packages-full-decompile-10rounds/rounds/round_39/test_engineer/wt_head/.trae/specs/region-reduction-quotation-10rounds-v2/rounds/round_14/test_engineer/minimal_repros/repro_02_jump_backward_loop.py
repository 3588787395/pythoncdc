"""复现 02：循环末尾 JUMP_BACKWARD 目标偏移差异。

模式：for 循环末尾的 JUMP_BACKWARD 跳回循环开头（FOR_ITER），orig 和 new 的
目标 offset 因指令布局差异相差 2 字节，但归一化为指令索引后指向同一 FOR_ITER。

对应函数：one_prod_to_dataframe @idx427 (JUMP_BACKWARD 1666 vs 1668)
"""
def f(items):
    result = []
    for x in items:
        if x > 0:
            result.append(x)
    return result
