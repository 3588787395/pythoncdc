"""repro_11: listcomp + `if not x == 5:` 外层守卫 + 两分支，跳转目标偏移（build_future_fill_time 变体）。

原始 build_future_fill_time 用 `if not typet == 5:` 外层守卫包裹多分支。listcomp 归约后
父分支 JUMP_FORWARD 跳转目标偏移。本 repro 用 `if not` 守卫 + 两分支（各含 listcomp +
嵌套 for append）聚焦 listcomp 跳转目标计算缺陷。
"""


def build_future_fill_time_guard(suffix, typet, start, end):
    trade_days = ['2019-01-01', '2019-01-02', '2019-01-03']
    total_dts = []
    if not typet == 5:
        if typet == 1:
            trade_times = ['09:30:00', '10:00:00', '10:30:00', '11:00:00']
            trade_times = [item.strftime(' %H:%M:%S') for item in trade_times]
            for today in trade_days:
                for item in trade_times:
                    total_dts.append(today + item)
        elif typet == 2:
            trade_times = ['09:35:00', '10:00:00', '10:30:00']
            trade_times = [item.strftime(' %H:%M:%S') for item in trade_times]
            for today in trade_days:
                for item in trade_times:
                    total_dts.append(today + item)
    return total_dts
