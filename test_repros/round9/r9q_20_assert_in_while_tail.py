def assert_in_while_tail(cond, n, lg):
    while cond:
        lg.info(n)
        assert n > 0, 'bad'
    return None
