def nested_while_for(dates, n, unit):
    i = 0
    j = 0
    indexes_strt = []
    indexes_end = []
    while j < n:
        same = dates[i] == dates[j]
        if not same:
            indexes_strt.append(i)
            indexes_end.append(j - 1)
            i = j
        j += 1
    if j == n:
        indexes_strt.append(i)
        indexes_end.append(j - 1)
    result_len = len(indexes_strt)
    for idx in range(result_len):
        print(dates[idx])
    return indexes_strt
