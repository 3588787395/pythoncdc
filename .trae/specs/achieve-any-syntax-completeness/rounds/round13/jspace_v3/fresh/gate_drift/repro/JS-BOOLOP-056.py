def f_b98_or_tail_and_group(a, b, c, d):
    for i in range(3):
        if i:
            if (a and b) or c or d:
                return i
    return 0
if __name__ == '__main__':
    print(f_b98_or_tail_and_group(1, 1, 1, 1))
