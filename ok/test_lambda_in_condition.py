def func(daterange, typet=6):
    if len(daterange) > 0:
        if typet == 1:
            result = [s.strftime('%Y-%m-%d %H:%M:%S') for s in daterange]
        else:
            result = [s.strftime('%Y-%m-%d') for s in daterange]
    else:
        return None
    return result
