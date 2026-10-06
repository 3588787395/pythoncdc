# Source Generated with Decompyle++ (Python version)
# File: e02_g1_b98_hosts.pyc (Python 3.11)

_P, _Q, _R, _S = 1, 2, 3, 4
M1 = (_P or _Q) and _R
M2 = _P or _Q and _R
class CB98:
    C1 = (_P or _Q) and _R
    C2 = _P or _Q and _R
    def m_handler(self, a, b, c):
        try:
            for i in range(3):
                if i:
                    return (a or b) and c
        except ValueError:
            if a:
                (a or b) and c
            else:
                return -1
        return 0
    def m_class_body_host(self, a, b, c):
        for i in range(2):
            if i:
                return a or b and c
        return 0
def f_comp_cond_host(a, b, c, xs):
    for i in range(2):
        if i:
            return [x for x in xs if a or b and c]
    return []
def f_genexp_cond_host(a, b, c, xs):
    for i in range(2):
        if i:
            return sum((1 for x in xs if a or b and c))
    return 0
def f_dictcomp_value_host(a, b, c, xs):
    for i in range(2):
        if i:
            return {b if not a else c: None for x in xs if x}
    return {}
def f_nested_func_host(a, b, c):
    def inner():
        for i in range(3):
            if i:
                if (a or b) and c:
                    pass
        return 0
    for j in range(2):
        if j:
            return inner()
    return 0
def f_match_arm_host(a, b, c, cmd):
    for i in range(2):
        if i:
            match cmd:
                case 1:
                    pass
                    return b and c
                case _:
                    return a or b and c
    return 0
def f_with_body_host(a, b, c):
    class CM:
        def __enter__(self):
            return self
        def __exit__(self, *e):
            return False
    with CM() as cm:
        for i in range(2):
            if i:
                if (a or b) and c:
                    pass
    return 0
def f_try_body_host(a, b, c):
    try:
        for i in range(2):
            if i:
                return (a or b) and c
    except KeyError:
        return -1
    return 0
