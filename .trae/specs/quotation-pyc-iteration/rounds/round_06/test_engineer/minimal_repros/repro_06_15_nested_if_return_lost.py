"""Repro 06-15: Lost return value expression in nested if inside except.

When an except handler contains a nested if/else where each branch
returns, the inner return value is emitted as a bare Expr instead of
a Return statement (the `return` keyword is lost).
"""


def handle(e2):
    try:
        process(e2)
    except ValueError as e:
        if e.code == 401:
            return ({'error': e}, None)
        else:
            return (None, {'ok': True})
    return None
