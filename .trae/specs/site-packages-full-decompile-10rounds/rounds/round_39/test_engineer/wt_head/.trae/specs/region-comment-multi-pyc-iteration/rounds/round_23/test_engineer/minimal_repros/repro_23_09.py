def while_else(n):
    i = 0
    while i < n:
        if i == 5:
            break
        i += 1
    else:
        return 'completed'
    return 'broken'
