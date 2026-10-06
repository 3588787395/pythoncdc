# Source Generated with Decompyle++ (Python version)
# File: r4_b109_shapes.pyc (Python 3.11)

def b109_else_fallthrough(xs):
    while xs:
        if len(xs) > 10:
            return None
        xs.pop()
    else:
        print('done')
        return None
def b109_else_return_none(xs):
    while xs:
        y = xs.pop()
        if y > 3:
            break
    else:
        return None
    return y
