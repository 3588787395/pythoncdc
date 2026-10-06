def b109_else_fallthrough(xs):
    while xs:
        if len(xs) > 10:
            break
        xs.pop()
    else:
        print('done')


def b109_else_return_none(xs):
    while xs:
        y = xs.pop()
        if y > 3:
            break
    else:
        return None
    return y