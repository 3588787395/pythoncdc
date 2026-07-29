"""repro_13: `if i == 0 and len(v) == N:` elif 链（3 分支变体，one_prod 最小化）。

最小化 one_prod_to_dataframe 的 elif 链分裂缺陷：仅保留 3 个 `if i == 0 and len(v) == N:` 分支，
去掉 try/except 和外层 for 循环，聚焦 elif 链分裂的核心模式。
"""


def one_prod_minimal(item):
    index = []
    i = 0
    for v in item:
        if i == 0 and len(v) == 8:
            index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} 00:00:00")
        elif i == 0 and len(v) == 10:
            index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:00:00")
        elif i == 0 and len(v) == 12:
            index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:{v[10:12]}:00")
        i = i + 1
    return index
