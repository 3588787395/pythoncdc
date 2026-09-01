
def test_multi_stmt_return(x):
    if x > 0:
        if x == 1:
            y = x
            z = x * 2
            return -1 * x
        else:
            old = x
            y = x - 1
            return old - y
    return 0
