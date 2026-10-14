def h(xs):
    total = 0
    for x in xs:
        try:
            total += int(x)
        except ValueError:
            total += 1
        print(total)
    return total
