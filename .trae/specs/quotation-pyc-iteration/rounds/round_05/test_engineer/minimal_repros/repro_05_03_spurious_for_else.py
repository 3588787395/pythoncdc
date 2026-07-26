# R5 minimal repro: spurious for-else 顺序语句误附加为 else 子句
# 关联缺陷：quotation.pyc one_prod_to_dataframe line 246-248 / load_get_index_stocks line 794-796 (R4 残留 #4)
# 触发区域：LOOP / _identify_loop_regions + _generate_loop (for 循环后顺序语句被误并入 else 子句)
# 预期：for item in fields: if i != t: df[k]=[]; i+=1
#       prod = data.get(prod_code)        <- 顺序语句
#       for item in prod: ...
# R5 实际产物：for item in fields: ... else: prod = data.get(prod_code); prod


def one_prod_to_dataframe(data, prod_code):
    df = {}
    fields = data.get('fields')
    time_index = 0
    i = 0
    for item in fields:
        if time_index != i:
            df[item] = []
        i = i + 1
    prod = data.get(prod_code)
    for item in prod:
        df[item] = item
    return df
