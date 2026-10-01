# Source Generated with Decompyle++ (Python version)
# File: r2_16_handler_complex_type.pyc (Python 3.11)

def f(exc, mod, table):
    out = []
    try:
        out.append(mod.value[0])
    except mod.errors.MyError(table['code']):
        out.append('custom')
    except mod.registry[1, 2]:
        out.append('sub')
    return out
def g(mod, name):
    try:
        return mod.handlers[name[0]]()
        return None
    except mod.registry.make(name[1]):
        return None
    except mod.base.TestErr:
        return 'direct'
