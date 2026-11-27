gvar = 7


def outer():
    x = 1; y = 2
    def inner():
        z = x
        comp = [i for i in range(3)]
        del z
        return x
    class C:
        ref = x          # LOAD_CLASSDEREF
        def m(self): return x
        del_cls = 1
    del y               # DELETE_DEREF
    return C, inner


del gvar
