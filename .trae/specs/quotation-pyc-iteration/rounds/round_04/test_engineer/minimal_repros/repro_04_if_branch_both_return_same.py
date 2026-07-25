# R4 minimal repro: if/elif/else 分支条件丢失, 两分支返回相同值
# 关联缺陷：新发现 (R4 新增, _is_same_type_date: if typet==7: return True else: return True)
# 触发区域：IF
# 预期：不同 typet 返回不同值 (含嵌套 if + 字符串比较)
# R4 实际产物：if typet == 7: return True else: return True (条件与返回值丢失)
def _is_same_type_date(day1, day2, typet):
    if typet == 7:
        if len(day1) == 10 and len(day2) == 10:
            return True
        else:
            return False
    elif typet == 6:
        if len(day1) == 8 and len(day2) == 8:
            return True
        else:
            return False
    else:
        return False
