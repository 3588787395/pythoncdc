"""repro_05: get_date_and_count while 循环 if/elif 链语句丢失 (-27)
区域类型: Loop + Conditional
违反原则: 1 (自底向上归约) + 3 (嵌套即抽象节点)
对应函数: get_date_and_count
缺陷镜像: while 循环体内 `if candle_period == 8: ... elif candle_period == 9: ... elif ... ` 链
  未完整生成，Loop+Conditional 嵌套归约时 elif 分支块作为子区域未被正确抽象，分支语句丢失。
  diff_detail first_diff_idx=140 (JUMP_FORWARD / POP_JUMP_FORWARD_IF_FALSE if 链入口处发散)。
"""


def f(candle_period, query_date):
    count = 0
    while count < 10:
        if candle_period == 8:
            year = query_date.year
            month = query_date.month
            query_date = fmt(query_date)
        elif candle_period == 9:
            query_date = fmt2(query_date)
        elif candle_period == 10:
            query_date = fmt3(query_date)
        else:
            query_date = fmt(query_date)
        count += 1
    return query_date


def fmt(d):
    return d


def fmt2(d):
    return d


def fmt3(d):
    return d
