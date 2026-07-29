"""repro_10: 复现 change_his_to_backward 反编译缺陷（FOR_ITER 目标过短 + 函数尾丢失 -56）。

缺陷模式：
    for n in indexlist:
        if int(firsttime) > 0: ...
    # 尾部数据处理代码丢失
FOR_ITER 目标计算过短，循环后数据操作代码全部丢失（orig=578, new=522, diff=-56）。

根因：FOR_ITER 跳转目标计算过短导致循环体提前收敛，循环后 `if/None` 尾部代码与
数据操作语句未被纳入函数体，函数尾部缺失。
"""


def change_his_to_backward(indexlist, firsttime):
    result = {}
    for n in indexlist:
        if int(firsttime) > 0:
            result[n] = process(n)
        else:
            result[n] = n
    data = manipulate(result)
    return data
