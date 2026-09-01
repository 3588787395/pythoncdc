def while_post_if(n):
    j = 0
    i = 0
    while j < n:
        if j % 2 == 0:
            i = j
        j += 1
    if j == n:
        return i
    return -1
