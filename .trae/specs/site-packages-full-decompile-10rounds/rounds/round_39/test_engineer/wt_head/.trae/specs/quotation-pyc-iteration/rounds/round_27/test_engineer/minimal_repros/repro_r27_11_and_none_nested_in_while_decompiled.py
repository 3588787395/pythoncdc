# Source Generated with Decompyle++ (Python version)
# File: repro_r27_11_and_none_nested_in_while.pyc (Python 3.11)

def f(a, b):
    if a is not None and b is None:
        return 1
    else:
        match a:
            case None:
                if b:
                    return 2
                else:
                    return 0
            case _:
                pass
