
def simple_while_else(x, data):
    if x > 0:
        while x > 0 and data:
            item = data.pop()
            x -= item
    else:
        if data:
            old = data.pop()
            return old
    return x
