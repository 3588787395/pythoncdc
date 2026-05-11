def func(count, flag, redata):
    while count < 3:
        if flag == 1:
            count += 1
        elif flag == -1:
            if redata:
                pass
            else:
                return None
        if redata:
            return redata
