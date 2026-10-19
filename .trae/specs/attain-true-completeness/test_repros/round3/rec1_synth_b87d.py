def s_b87d(rows):
    total = 0
    try:
        for r in rows:
            try:
                for c in r:
                    total += c
            finally:
                total -= 1
    except TypeError:
        return -1
    return total
