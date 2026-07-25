# R4 minimal repro: Call 实参位置的 IfExp 畸形重构
# 关联缺陷：新发现 (R4 新增, get_history: FREQUENCYNAME_DICT(query_date is None if frequency in OVER_WEEK_FREQUENCY else query_date is None))
# 触发区域：TERNARY + CALL
# 预期：含 if/elif/else + 多变量赋值 + return 的完整函数体
# R4 实际产物：Call 实参为畸形 IfExp (双臂均为 query_date is None, 丢失 in/== 比较)
def get_history(count, frequency='1d', field=None, security_list=None, fq=None, query_date=None):
    ClearAllCache()
    if count <= 0:
        strategy_log.error('count不能小于等于0')
        return None
    is_string = False
    if security_list is None:
        strategy_log.error('未传入security_list')
        return None
    elif isinstance(security_list, str):
        is_string = True
        security_list = [security_list]
    if frequency in OVER_WEEK_FREQUENCY:
        if query_date is None:
            strategy_log.error('周期查询必须指定 query_date')
            return None
        nd_array = FREQUENCYNAME_DICT.get(frequency)
    else:
        nd_array = FREQUENCYNAME_DICT.get(frequency)
    return nd_array
