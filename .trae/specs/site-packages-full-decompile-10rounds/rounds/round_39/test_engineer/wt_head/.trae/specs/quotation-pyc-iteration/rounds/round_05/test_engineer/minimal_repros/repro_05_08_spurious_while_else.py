# R5 minimal repro: spurious while-else 顺序语句误附加为 while-else 子句
# 关联缺陷：quotation.pyc get_date_and_count line 906-910 / 965-969 / 978-981 (新发现)
# 触发区域：LOOP / _identify_loop_regions + _generate_loop (while 循环后顺序语句被误并入 else 子句)
# 预期：while count > 0: if m-c<=0: ... else: ...
#       if m in (10,11,12): s = str(y)+str(m)+'01'   <- 顺序语句
#       else: s = str(y)+'0'+str(m)+'01'
# R5 实际产物：while count > 0: ... else: if m in (10,11,12): s = ...  (顺序语句被误并入 while-else)


def get_date_and_count(count, month, year):
    start_date = None
    while count > 0:
        if month - count <= 0:
            year -= 1
            count -= month
            month = 12
        else:
            month = month - count
            count = 0
    if month in (10, 11, 12):
        start_date = str(year) + str(month) + '01'
    else:
        start_date = str(year) + '0' + str(month) + '01'
    return (start_date, year, month)
