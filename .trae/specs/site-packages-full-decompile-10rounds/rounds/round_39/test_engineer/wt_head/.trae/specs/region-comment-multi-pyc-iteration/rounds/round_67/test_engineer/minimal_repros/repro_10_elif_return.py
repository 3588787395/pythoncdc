
def test_elif_return(x):
    if x == 1:
        y = x
        return -1 * x
    elif x == 2:
        old = x
        return old - x
    return 0
