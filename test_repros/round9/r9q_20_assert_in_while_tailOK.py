# Source Generated with Decompyle++ (Python version)
# File: r9q_20_assert_in_while_tail.pyc (Python 3.11)

def assert_in_while_tail(cond, n, lg):
    while cond:
        lg.info(n)
        assert n > 0, 'bad'
    return None
