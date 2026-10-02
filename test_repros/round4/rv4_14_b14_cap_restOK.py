# Source Generated with Decompyle++ (Python version)
# File: rv4_14_b14_cap_rest.pyc (Python 3.11)

def seq_multi_cap(xs):
    """V1: sequence patterns with multiple captures, bodies reordering them."""
    match xs:
        case [a, b, c]:
            return (a, b, c)
        case [p, q]:
            return (q, p)
        case other:
            return ('rest', other, 0)
def map_rest_mix(d):
    """V2: mapping with named captures plus **rest, followed by capture-tail case."""
    match d:
        case {'a': aa, 'b': bb, **rest}:
            return (aa, bb, sorted(rest.keys()))
        case {'z': zval}:
            return ('z', zval)
        case other2:
            return ('map-rest', other2)
def seq_cap_and_map(xs):
    """V3: sequence capture case and mapping capture case in one match."""
    match xs:
        case [one, two]:
            return ('pair', one, two)
        case {'head': h, **tail}:
            return ('map', h, len(tail))
        case _:
            return 0
