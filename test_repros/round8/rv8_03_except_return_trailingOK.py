# Source Generated with Decompyle++ (Python version)
# File: rv8_03_except_return_trailing.pyc (Python 3.11)

def except_return_none_then_trailing(x):
    try:
        v = int(x)
    except ValueError:
        print('bad')
        return None
    return v + 1
def except_pass_trailing_implicit(x):
    try:
        v = int(x)
    except ValueError:
        pass
    return v
def two_handlers_shared_tail(x):
    try:
        v = int(x)
    except ValueError:
        v = 0
    except TypeError:
        v = 1
    return v
def try_body_return_then_except(x):
    try:
        return 1
    except ValueError:
        return 2
def handler_return_value_then_trailing(x):
    try:
        v = int(x)
    except ValueError:
        return 0
    except TypeError:
        return None
    return v
