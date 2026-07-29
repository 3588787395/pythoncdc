"""repro_05: listcomp + 嵌套 for append，父分支 JUMP_FORWARD 跳转目标偏移（build_future_fill_time）。

原始 build_future_fill_time：listcomp 归约后父循环 JUMP_FORWARD 2660→2586（偏移 74 字节）。
反编译器在 listcomp 区域归约后未同步父分支跳转目标，导致 instr_diff。本 repro 聚焦
listcomp + 嵌套 for + elif 分支跳转目标计算缺陷。
"""


def build_future_fill_time(suffix, typet, start, end):
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
