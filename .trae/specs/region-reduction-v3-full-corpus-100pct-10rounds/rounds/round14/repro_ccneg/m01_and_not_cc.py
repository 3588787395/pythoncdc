def g(include, frequency, cur_datetime, min_datetime, pm_open, am_close, pm_close, time_count, count):
    if not include and frequency == 'MIN' and cur_datetime not in (min_datetime, pm_open):
        if not (pm_open > cur_datetime > am_close) and not (cur_datetime > pm_close):
            time_count -= 1
        if frequency == 'MIN' and time_count > count:
            return 1
    return 0
