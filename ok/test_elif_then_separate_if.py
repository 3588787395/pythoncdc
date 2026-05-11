def func(data, start, end):
    if len(data) == 0:
        return data
    elif start != 'firstdate':
        start = 'firstdate'
    if len(start) > 8:
        start = start[:8]
        if len(end) > 8:
            end = end[:8]
    return (start, end)
