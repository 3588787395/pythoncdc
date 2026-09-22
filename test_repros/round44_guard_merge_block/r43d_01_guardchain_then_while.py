def r43d_01_guardchain_then_while(index, key):
    l = len(index)
    if l == 0:
        return 0
    start, end = 0, l - 1
    if index[start] > key:
        return 0
    if key >= index[end]:
        return end + 1
    while end - start > 1:
        middle = (start + end) // 2
        m = index[middle]
        if m == key:
            return middle + 1
        elif m < key:
            start = middle
        else:
            end = middle
    return end
