def g(gx):
    return gx


def h(gx):
    return gx

for x in (1, 2):
    if x:
        try:
            g(x)
        except BaseException:
            h(x)
