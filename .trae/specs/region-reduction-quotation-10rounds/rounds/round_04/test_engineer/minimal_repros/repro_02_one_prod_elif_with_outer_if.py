"""repro_02: `if i == 0 and len(v) == N:` elif 链外包 `elif time_index is not None:`（one_prod 变体）。

镜像 one_prod_to_dataframe 的实际 CFG 嵌套结构：elif 链位于 `elif time_index is not None:` 分支内，
且分支内含 `v = str(v)` 前序赋值。本变体验证前序赋值 + 嵌套 elif 是否影响 elif 链归约。
"""


def one_prod_variant(fields, prod):
    index = []
    time_index = 0
    for item in prod:
        i = 0
        for v in item:
            if time_index != i:
                pass
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
            i = i + 1
    return index
