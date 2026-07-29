"""repro_09: 多 elif 分支 + listcomp + 嵌套 for append + JUMP_FORWARD 偏移（build_future_fill_time）。

原始 build_future_fill_time 结构：
    if not typet == 5:
        if typet == 1:
            trade_times = [item.strftime(' %H:%M:%S') for item in trade_times]
            for today in trade_days:
                for item in trade_times:
                    total_dts.append(today + item)
        elif typet == 2:
            ...
反编译后唯一差异 JUMP_FORWARD 2660→2586（偏移 74 字节）。listcomp 归约后父区域
跳转目标未同步。本 repro 聚焦 listcomp + 嵌套 for 跳转目标计算缺陷。
"""


def build_future_fill_time(suffix, typet, start, end):
    trade_days = ['2019-01-01', '2019-01-02', '2019-01-03']
    total_dts = []
    if not typet == 5:
        if typet == 1:
            market_time = {'open_am': '09:30:00', 'close_am': '11:30:00', 'freq': 'T'}
            trade_times = ['09:30:00', '10:00:00', '10:30:00', '11:00:00']
            trade_times = [item.strftime(' %H:%M:%S') for item in trade_times]
            for today in trade_days:
                for item in trade_times:
                    total_dts.append(today + item)
        elif typet == 2:
            if suffix == 'T.CCFX':
                market_time = {'open_am': '09:35:00', 'close_am': '11:30:00', 'freq': '5T'}
            else:
                market_time = {'open_am': '09:35:00', 'close_am': '11:30:00', 'freq': '5T'}
            trade_times = ['09:35:00', '10:00:00', '10:30:00', '11:00:00']
            trade_times = [item.strftime(' %H:%M:%S') for item in trade_times]
            for today in trade_days:
                for item in trade_times:
                    total_dts.append(today + item)
        elif typet == 3:
            trade_times = ['09:45:00', '10:00:00', '10:15:00']
            trade_times = [item.strftime(' %H:%M:%S') for item in trade_times]
            for today in trade_days:
                for item in trade_times:
                    total_dts.append(today + item)
    return total_dts
