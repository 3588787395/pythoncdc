def r11_multilevel_attr(o):
    o.a.b = (r := make())
    return r
def make():
    return 11
