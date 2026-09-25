MINUTE = '1m'


def guard(include, frequency, cur_datetime, min_datetime, pm_open, am_close, pm_close, time_count):
    if not include and frequency == MINUTE and cur_datetime not in (min_datetime, pm_open) and not (
            pm_open > cur_datetime > am_close or cur_datetime > pm_close):
        time_count -= 1
    if frequency == MINUTE:
        out = time_count
        if out > 10:
            out = 10
    elif frequency == '5m':
        out = time_count // 5
    else:
        out = time_count // 60
    return out
