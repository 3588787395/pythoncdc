def r04_attr_call(obj):
    obj.x = (r := make())
    return r
def make():
    return 7
