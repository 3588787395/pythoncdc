"""repro_14: nested try/except inside for-loop, post-loop assignment (no return).

    Variant where post-loop code is an assignment (not return), to test
    that post-loop fall-through code is correctly placed OUTSIDE the loop
    and the outer except is correctly generated.
"""
def f(items):
    result = []
    try:
        for x in items:
            try:
                result.append(int(x))
            except ValueError:
                result.append(0)
        total = sum(result)
    except BaseException:
        total = -1
    return total
