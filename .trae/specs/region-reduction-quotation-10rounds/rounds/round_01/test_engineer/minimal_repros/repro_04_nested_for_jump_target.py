"""repro_04: 嵌套 for + listcomp + if/elif 跳转目标偏移（build_future_fill_time 模式）。

复现原始字节码结构：嵌套 for 循环 + listcomp 推导式 + 循环后 if/elif 链。
反编译器 JUMP_FORWARD 目标偏移（2660→2586），指令数相同但跳转错误。
对应 _identify_loop_regions 嵌套 + _identify_conditional_regions 跳转目标。
"""


def build_future_fill_time(suffix, typet, start, end, items, total_dts):
    for item in items:
        for sub in item:
            total_dts.append(sub)
    times = [t for t in total_dts if t is not None]
    if typet == 2:
        if suffix == 'T.CCFX':
            open_am = '09:35:00'
            close_am = '11:30:00'
            open_pm = '13:00:00'
            close_pm = '15:00:00'
        else:
            open_am = '09:30:00'
            close_am = '11:30:00'
            open_pm = '13:00:00'
            close_pm = '15:00:00'
    elif typet == 1:
        open_am = '09:30:00'
        close_am = '11:30:00'
        open_pm = '13:00:00'
        close_pm = '15:00:00'
    else:
        open_am = '09:30:00'
        close_am = '15:00:00'
        open_pm = None
        close_pm = None
    return [open_am, close_am, open_pm, close_pm]
