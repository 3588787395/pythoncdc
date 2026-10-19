def s_b133a(xs):
    total = 0
    for i in xs:
        for j in xs:
            if j:
                continue
            else:
                break
        else:
            total += 1
    return total
