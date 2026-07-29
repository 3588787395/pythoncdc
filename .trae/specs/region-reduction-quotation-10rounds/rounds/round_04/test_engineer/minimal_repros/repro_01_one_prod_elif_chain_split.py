"""repro_01: `if i == 0 and len(v) == N:` elif 链被拆分为两个 if 结构（one_prod_to_dataframe）。

R4 重点目标：one_prod_to_dataframe +11 指令。原始函数含 5 个 `if i == 0 and len(v) == N:` elif 分支，
反编译器将 `i == 0` 拆为外层 if，`len(v) == N` 拆为内层 if，导致 elif 链分裂、部分条件丢失、body 丢失为 pass。

本 repro 镜像 one_prod_to_dataframe 的实际 CFG：
  - 外层 for item in prod: 循环
  - 内层 for v in item: 循环
  - if time_index != i: ... elif time_index is not None: v = str(v); if i == 0 and len(v) == N: ...
  - 5 个 len(v) == N 的 elif 分支（N = 8, 10, 11, 12, 14）
"""


def one_prod_to_dataframe_repro(data, prod_code, data_type=None):
    df = {}
    fields = data.get('fields')
    index = []
    time_index = None
    try:
        time_index = fields.index('business_time')
    except BaseException:
        system_log.error(get_traceback_message())
    try:
        time_index = fields.index('min_time')
    except BaseException:
        system_log.error(get_traceback_message())
    i = 0
    for item in fields:
        if time_index != i:
            df[get_real_param(item)] = []
        i = i + 1
    prod = data.get(prod_code)
    for item in prod:
        i = 0
        for v in item:
            if time_index != i:
                df[get_real_param(fields[i])].append(v)
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
    columns = []
    if data_type is None:
        i = 0
        for item in fields:
            if time_index != i:
                columns.append(get_real_param(item))
            i = i + 1
    else:
        columns = ['open', 'close', 'high', 'low', 'volume', 'money']
    return pandas.DataFrame(df, columns=columns, index=index)
