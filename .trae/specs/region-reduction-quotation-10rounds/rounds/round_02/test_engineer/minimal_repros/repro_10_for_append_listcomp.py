"""repro_10: for + append + JUMP_BACKWARD + listcomp 跳转目标（build_future_fill_time）。

原始 build_future_fill_time 在嵌套 for 内 `total_dts.append(today + item)` 后
JUMP_BACKWARD 回循环头，循环结束后 JUMP_FORWARD 跳到 typet 判定。反编译器在循环后
JUMP_FORWARD 目标计算偏移 74 字节。本 repro 聚焦 listcomp 归约后父循环跳转目标偏移。
"""


def build_fill_time(suffix, typet, start, end):
    total_dts = []
    items = [1, 2, 3, 4, 5]
    for item in items:
        if typet == 2:
            times = ['09:35:00', '11:30:00', '13:30:00', '15:00:00']
        elif typet == 6:
            times = [str(x) for x in range(10) if x > 2]
        else:
            times = [str(x) for x in range(5)]
        for t in times:
            total_dts.append(t)
    result = [d for d in total_dts if d != '']
    return result
