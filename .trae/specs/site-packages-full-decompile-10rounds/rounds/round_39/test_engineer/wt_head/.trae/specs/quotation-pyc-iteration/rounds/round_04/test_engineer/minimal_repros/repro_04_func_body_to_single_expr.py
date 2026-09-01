# R4 minimal repro: 函数体被替换为单个 Expr 语句 (含 IfExp)
# 关联缺陷：新发现 (R4 新增, date_convert orig=87 new=16)
# 触发区域：TERNARY + IF
# 预期：含 if/elif + return 的完整函数体
# R4 实际产物：int(month_temp == 1 if report_types is None else month_temp <= report_types)  (单 Expr)
def date_convert(date, report_types):
    month_temp = int(date[4:6])
    if report_types is None:
        if month_temp == 1:
            year = int(date[:4]) - 1
            month = 12
        else:
            year = int(date[:4])
            month = month_temp - 1
    else:
        if month_temp <= report_types:
            year = int(date[:4]) - 1
            month = 12 - (report_types - month_temp)
        else:
            year = int(date[:4])
            month = month_temp - report_types
    return '%04d%02d' % (year, month)
