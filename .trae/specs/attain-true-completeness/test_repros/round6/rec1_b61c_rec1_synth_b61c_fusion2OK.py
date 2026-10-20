# Source Generated with Decompyle++ (Python version)
# File: rec1_b61c_rec1_synth_b61c_fusion2.pyc (Python 3.11)

__doc__ = 'R5 synth family 3a: case capture fusion (mapping rest / tuple / class as) with leading if on captures (B61c).'
def f2_map(x):
    match x:
        case {'op': op, **rest}:
            if 'k' in rest:
                del rest['k']
            return (op, rest)
        case [p, q]:
            if p:
                return p
            else:
                return q
        case _:
            raise TypeError('bad')
def f2_cls(x):
    match x:
        case int() as v:
            if v > 0:
                return v
            else:
                return -v
        case _:
            return 0
