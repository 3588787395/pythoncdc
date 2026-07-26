"""Repro 09-08: D7 variant — IfExp in Call argument position.

The D7 root cause is that _generate_if / IfExp reconstruction
compresses if/elif chains into nested ternary. When the if/elif chain
appears as a Call argument, the IfExp is preserved (correct), but
when it appears as a statement-level if/elif, it is incorrectly
compressed. This repro tests the boundary: a Call whose argument is
an if/elif/else expression (correct IfExp) vs a statement-level
if/elif/else assignment (D7 defect).

Expected defect: the statement-level if/elif/else is compressed to a
bare Expr of nested ternary of `==`; the Call-arg IfExp is preserved.
"""


def classify(x):
    # Statement-level if/elif/else (D7 should fire here)
    if x == 1:
        y = 'a'
    elif x == 2:
        y = 'b'
    else:
        y = 'c'
    # Call with IfExp argument (should be preserved)
    log('result: %s' % ('high' if x > 0 else 'low'))
    return y
