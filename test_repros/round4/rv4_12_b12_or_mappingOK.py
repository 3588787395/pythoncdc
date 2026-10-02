# Source Generated with Decompyle++ (Python version)
# File: rv4_12_b12_or_mapping.pyc (Python 3.11)

def or_map_nested(d):
    """V1: or alternatives are mapping/sequence shapes (same-bound-names)."""
    match d:
        case {'a': 1}:
            pass
        case {'a': 2}:
            pass
        case {'a': 1}:
            pass
        case {'b': [_, _]}:
            pass
        case _:
            return 'no'
def or_as_capture(d):
    """V2: or of literals with as-capture; or of shapes with as-capture."""
    match d:
        case 1 | 2:
            return ('num', v)
        case {'k': 2}:
            pass
        case {'k': _, 'j': _}:
            pass
        case _:
            return 'other'
    return ('shape', w)
def or_mixed_deep(d):
    """V3: three alternatives mixing nested mapping and starred sequence."""
    match d:
        case {'x': {'y': 1}}:
            pass
        case {'x': {'y': 2}}:
            pass
        case [1, 2]:
            return 'deep-or'
        case _:
            return 'no'
