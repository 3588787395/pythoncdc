def while_loop_with_break(n, limit):
    j = 0
    i = 0
    while j < n:
        if j > limit:
            break
        j += 1
    return i, j
