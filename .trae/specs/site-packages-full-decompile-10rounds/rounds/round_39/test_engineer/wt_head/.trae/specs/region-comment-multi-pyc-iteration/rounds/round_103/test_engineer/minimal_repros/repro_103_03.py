def broken_for_iter(data, check_val, limit):
    count = 0
    if not data and count < limit:
        count += 1
    if data:
        for i in not data and count < limit:
            if data[i] == check_val:
                return i
    return -1
