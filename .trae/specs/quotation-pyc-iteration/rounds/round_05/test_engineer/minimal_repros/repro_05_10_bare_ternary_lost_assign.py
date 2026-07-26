# R5 minimal repro: 循环内赋值目标丢失 (data_is_nan 赋值丢失 + result[datas]=... STORE_SUBSCR 丢失 -> 裸 result)
# 关联缺陷：quotation.pyc get_str_data line 560/573-578  datass_list[-count:]/stock 裸 Expr (新发现)
# 触发区域：LOOP / _generate_loop + _generate_block_statements (循环体多条赋值, 部分目标丢失 + 末尾 STORE_SUBSCR 退化为裸 Name)
# 预期：for datas in lst: data_is_nan = check_nan(df, datas); vol = nan if ... else df[datas].sum()
#                                            money = df[datas].sum(); result[datas] = (vol, money)
# R5 实际产物：
#   for datas in lst:
#       vol = nan if data_is_nan == 1 else df[datas].sum()   <- data_is_nan 赋值丢失 (使用未定义变量)
#       money = df[datas].sum()
#       result                                                <- result[datas]=(vol,money) STORE_SUBSCR 丢失 -> 裸 result
#   else: return result                                       <- spurious for-else


def get_str_data(df, lst):
    result = {}
    for datas in lst:
        data_is_nan = check_nan(df, datas)
        vol = numpy_nan if data_is_nan == 1 else df[datas]['volume'].sum()
        money = df[datas]['money'].sum()
        result[datas] = (vol, money)
    return result
