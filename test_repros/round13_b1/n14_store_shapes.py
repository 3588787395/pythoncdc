gg: int = 1            # SETUP_ANNOTATIONS（模块首条注解）
g2 = 2
def ss(obj, seq):
    global gg
    gg = 3
    a: int = 1; b, c = 2, 3
    obj.attr = 1; obj[0] = 2; obj[1:2] = 3
    e = f = h = 4
    *i, j = seq
    del gg_local_only
    return a
del g2                 # DELETE_GLOBAL
class K:
    ka = 1
    del ka
