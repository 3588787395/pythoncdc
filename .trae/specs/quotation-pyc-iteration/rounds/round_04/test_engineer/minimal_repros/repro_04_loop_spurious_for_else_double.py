# R4 minimal repro: spurious for-else 误附加顺序语句为 else 子句
# 关联缺陷：repro_03_loop_spurious_for_else_double (P2 残留)
# 触发区域：LOOP
# 预期：for item in fields: if time_index != i: df[...]=[]; i+=1
#       prod = data.get(prod_code)   <- 顺序语句
#       for item in prod: ...
# R4 实际产物：for item in fields: ... else: prod = data.get(prod_code)
def one_prod_to_dataframe(data, prod_code):
    df = {}
    fields = data.get('fields')
    index = []
    time_index = None
    try:
        time_index = fields.index('business_time')
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
            i = i + 1
    return df
