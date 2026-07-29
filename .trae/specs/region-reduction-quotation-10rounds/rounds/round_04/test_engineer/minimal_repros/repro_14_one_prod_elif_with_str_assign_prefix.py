"""repro_14: `if i == 0 and len(v) == N:` elif 链 + 前序 `v = str(v)` 赋值（one_prod 变体 3）。

镜像 one_prod_to_dataframe 的 elif 链前序 `v = str(v)` 赋值对 elif 链归约的影响。
前序赋值位于 elif 链所在分支体的开头，可能干扰条件块的归属判定。
"""


def one_prod_with_prefix(item, time_index):
    index = []
    i = 0
    for v in item:
        if time_index != i:
            pass
        else:
            v = str(v)
            if i == 0 and len(v) == 8:
                index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} 00:00:00")
            elif i == 0 and len(v) == 10:
                index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:00:00")
            elif i == 0 and len(v) == 11:
                index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} 0{v[8:9]}:{v[9:11]}:00")
            elif i == 0 and len(v) == 14:
                index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:{v[10:12]}:{v[12:14]}")
        i = i + 1
    return index
