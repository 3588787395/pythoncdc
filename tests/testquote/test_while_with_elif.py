def func(count, flag, redata):
    while count < 3:
        if flag == 1:
            count += 1
        elif flag == -1:
            count -= 1
        else:
            if redata:
                return redata
        count += 1
    return None
