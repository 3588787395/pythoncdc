def walrus_while(n):
    j = (i := 0)
    while j < n:
        i = j
        j += 1
    return i
