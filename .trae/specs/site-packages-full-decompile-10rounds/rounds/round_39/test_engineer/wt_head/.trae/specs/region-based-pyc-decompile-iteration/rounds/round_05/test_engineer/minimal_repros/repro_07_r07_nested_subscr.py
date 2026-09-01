def r07_nested_subscr(a, b, c):
    a[b][c] = (r := make())
    return r
def make():
    return 1
