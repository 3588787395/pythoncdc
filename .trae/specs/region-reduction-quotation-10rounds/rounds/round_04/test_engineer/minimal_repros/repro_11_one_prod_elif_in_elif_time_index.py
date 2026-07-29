"""repro_11: `if i == 0 and len(v) == N:` elif 链位于 `elif time_index is not None:` 分支内（one_prod 变体 2）。

进一步镜像 one_prod_to_dataframe 的实际 CFG：elif 链位于 `elif time_index is not None:` 分支内，
且 `elif time_index is not None:` 分支内含 `v = str(v)` 赋值后接 5 个 `if i == 0 and len(v) == N:` elif 分支。
本变体去掉 try/except 简化，聚焦 elif 链在 elif 分支内的归约行为。
"""


def one_prod_variant_no_try(fields, prod):
    df = {}
    index = []
    time_index = 0
    i = 0
    for item in fields:
        if time_index != i:
            df[item] = []
        i = i + 1
    for item in prod:
        i = 0
        for v in item:
            if time_index != i:
                df[fields[i]].append(v)
            elif time_index is not None:
                v = str(v)
                if i == 0 and len(v) == 8:
                    index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} 00:00:00")
                elif i == 0 and len(v) == 10:
                    index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:00:00")
                elif i == 0 and len(v) == 11:
                    index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} 0{v[8:9]}:{v[9:11]}:00")
                elif i == 0 and len(v) == 12:
                    index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:{v[10:12]}:00")
                elif i == 0 and len(v) == 14:
                    index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:{v[10:12]}:{v[12:14]}")
            i = i + 1
    return (df, index)
