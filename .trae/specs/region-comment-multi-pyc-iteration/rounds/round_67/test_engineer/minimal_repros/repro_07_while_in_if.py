
def test_while_in_if(x, data):
    if x > 0:
        if x == 1:
            while x > 0 and data:
                item = data.pop()
                x -= item
        else:
            if data:
                old = data.pop()
                return old
    return x
