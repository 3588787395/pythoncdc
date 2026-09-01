# R5 minimal repro: elif 链分支嵌套 if (含 and/or boolop) 整块丢失 / 错误合并 -> if typet == 8: pass
# 关联缺陷：quotation.pyc _is_same_type_date line 583-584  if typet == 7: pass (R4 残留 #2 同源)
# 触发区域：IF / _generate_if + _identify_boolop_regions (嵌套 if 含 and/or boolop 时被错误合并到外层条件 + 体丢失)
# 预期：if typet == 7: if len(day1)==8 or len(day1)==10: return True  else: return False
#       elif typet == 8: if day1.year==day2.year and day1.month==day2.month: return True  else: return False
# R5 实际产物：
#   if typet == 7 and len(day1) == 8 or len(day1) == 10:   <- 嵌套 if 被错误合并 (优先级丢失, 应为 t==7 and (... or ...))
#       return True
#   else:
#       return False
#   if typet == 8: pass                                    <- and-boolop 分支体整块丢失


def _is_same_type_date(day1, day2, typet):
    if typet == 7:
        if len(day1) == 8 or len(day1) == 10:
            return True
        else:
            return False
    elif typet == 8:
        if day1.year == day2.year and day1.month == day2.month:
            return True
        else:
            return False
    elif typet == 9:
        if day1.year == day2.year:
            return True
        else:
            return False
    return False
