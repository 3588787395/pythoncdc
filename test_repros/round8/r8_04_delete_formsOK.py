# Source Generated with Decompyle++ (Python version)
# File: r8_04_delete_forms.pyc (Python 3.11)

__doc__ = 'R8-04 Delete forms: local / subscript / slice / attribute / multi-target / tuple-target / then-use / deep host.'
def r8_del_local():
    a = 1
    del a
    return 2
def r8_del_subscript(xs):
    del xs[0]
    return xs
def r8_del_slice(xs):
    del xs[1:3]
    return xs
def r8_del_attr(obj):
    del obj.x
    return obj
def r8_del_multi():
    a = 1
    b = 2
    del a
    del b
    return 3
def r8_del_tuple_target():
    a = 1
    b = 2
    del a
    del b
    return 4
def r8_del_then_use(xs):
    d = {'k': 1}
    del d['k']
    d['j'] = 2
    return d
def r8_del_in_loop(xs):
    out = []
    for i in range(len(xs)):
        if i % 2 == 0:
            del xs[i]
            continue
        out.append(xs[i])
        continue
    return out
def r8_del_nested_host(d):
    if d:
        for k in sorted(d):
            if k.startswith('tmp'):
                del d[k]
    return d
