def s_b133b(xs):
    total = 0
    for i in xs:
        j = i
        while j:
            if j == 2:
                break
            j -= 1
        else:
            total += 100
    return total
