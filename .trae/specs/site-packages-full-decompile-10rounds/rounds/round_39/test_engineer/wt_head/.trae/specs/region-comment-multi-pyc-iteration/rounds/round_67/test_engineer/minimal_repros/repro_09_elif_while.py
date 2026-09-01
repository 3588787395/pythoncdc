
def test_elif_while(x, data):
    if x == 1:
        while x > 0 and data:
            item = data.pop()
            x -= item
    elif x == 2:
        if data:
            return data.pop()
    return x
