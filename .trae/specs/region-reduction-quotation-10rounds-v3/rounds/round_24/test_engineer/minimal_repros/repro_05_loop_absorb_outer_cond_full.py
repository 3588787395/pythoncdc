"""repro_05 — 缺陷2: LOOP 反向链吸收外层条件块 + loop_else。

模式（取自 get_date_and_count 的 candle_period==8 分支）：
  if/elif/else 链，then 与 else 分支均含 `while count>0:` 循环 + `if month in (...)`
  条件块，每个分支末尾 JUMP_FORWARD 到 return。elif 分支简单赋值。
  反编译器把 else 分支的 while 循环反向链当作 loop_else，丢弃 while 包装，
  把 `count>0` 条件并入 elif 守卫，丢失 `count -= 1`，并多出兄弟 if/else。
"""
def f(flag, count):
    month = 5
    year = 2020
    if flag == 0:
        while count > 0:
            if month - count <= 0:
                year -= 1
                count -= month
                month = 12
            else:
                month = month - count
                count = 0
        if month in (10, 11, 12):
            start = str(year) + str(month)
        else:
            start = str(year) + '0' + str(month)
    elif count == 1:
        start = 'X'
    else:
        count -= 1
        while count > 0:
            if month - count <= 0:
                year -= 1
                count -= month
                month = 12
            else:
                month = month - count
                count = 0
        if month in (10, 11, 12):
            start = str(year) + str(month)
        else:
            start = str(year) + '0' + str(month)
    return (start, year)
