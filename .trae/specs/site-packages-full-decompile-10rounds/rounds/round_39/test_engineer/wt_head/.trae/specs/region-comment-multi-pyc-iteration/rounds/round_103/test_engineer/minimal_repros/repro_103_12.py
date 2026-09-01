def nested_if_else_shift(x, y, z):
    if x > 0:
        if y > 0:
            return 'a'
        else:
            return 'b'
    elif z > 0:
        return 'c'
    else:
        return 'd'
