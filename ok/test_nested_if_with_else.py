def func(stocks, typet, start, end):
    data = {}
    if isinstance(stocks, list):
        if len(start) > 8:
            tmp_start = start[:8]
            if len(end) > 8:
                tmp_end = end[:8]
            else:
                tmp_end = end
        else:
            tmp_start = start
    return data
