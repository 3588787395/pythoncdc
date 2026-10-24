# Source Generated with Decompyle++ (Python version)
# File: n9v9_stmt_sweep.pyc (Python 3.11)

def raise_deep(a, b):
    for i in range(3):
        try:
            if a > b:
                raise ValueError(i)
        except ValueError:
            a -= 1
    return a
def raise_from(a, b):
    with open('x') as f:
        try:
            raise KeyError(a) from TypeError(b)
        except KeyError:
            return a
    return b
def assert_deep(a, b):
    for i in range(3):
        while a < b:
            assert 0 < a < b, a
            a += 1
    return a
def pass_arms(a, b):
    try:
        if a > b:
            pass
        else:
            a = b
    except OSError:
        pass
    finally:
        pass
    return a
def expr_stmt_deep(a, b, sink):
    for i in range(2):
        with open('y') as f:
            sink(f.read())
            f'got {a} and {b!r}'
