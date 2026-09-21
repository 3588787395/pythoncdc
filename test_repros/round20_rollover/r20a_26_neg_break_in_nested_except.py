import sys


def break_in_except_nested(it, g):
    for x in it:
        try:
            g(x)
        except OSError:
            try:
                g(0)
            except ValueError:
                break
    g(1)
