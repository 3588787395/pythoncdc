def try_in_while(data, n):
    i = 0
    result = []
    while i < n:
        try:
            result.append(data[i])
        except IndexError:
            result.append(None)
        i += 1
    return result
