def r09_method_value(d, k, obj):
    d[k] = (r := obj.method())
    return r
