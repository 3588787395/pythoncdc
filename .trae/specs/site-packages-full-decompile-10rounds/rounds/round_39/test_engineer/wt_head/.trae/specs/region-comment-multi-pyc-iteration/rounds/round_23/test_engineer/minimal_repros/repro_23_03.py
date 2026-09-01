def while_nested_if_elif(bars, unit, n):
    j = 0
    i = 0
    start = []
    end = []
    while j < n:
        same = bars[j] == unit
        if not same:
            start.append(i)
            end.append(j - 1)
            i = j
        j += 1
    if j == n:
        start.append(i)
        end.append(j - 1)
    else:
        return []
    return (start, end)
