# Source Generated with Decompyle++ (Python version)
# File: r9q_02_assert_else_implicit_tail.pyc (Python 3.11)

def check(n):
    if n not in ('w', 'mo'):
        try:
            tmp = int(n)
        except BaseException:
            assert False, 'bad int'
        else:
            assert tmp > 0, 'bad pos'
        return None
