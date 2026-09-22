def w2(items):
    total = 0
    for n in items:
        if n != 0:
            if n > 10:
                if n % 2:
                    if n > 90:
                        total += n
                        continue
                    else:
                        total -= n
                        continue
                else:
                    total += 1
            else:
                total += 2
        else:
            total = 0
        if total > 100:
            total = 100
        total = total + n
    return total
