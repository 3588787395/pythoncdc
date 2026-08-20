def process_until_zero(values):
    total = 0
    i = 0
    while i < len(values):
        try:
            total += int(values[i])
        except ValueError:
            pass
        finally:
            i += 1
    return total
