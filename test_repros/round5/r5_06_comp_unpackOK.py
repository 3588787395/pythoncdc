# Source Generated with Decompyle++ (Python version)
# File: r5_06_comp_unpack.pyc (Python 3.11)

def u_star_body(pairs):
    return [[*a] for a in pairs]
def u_tuple_target(pairs):
    return [a + b for a, b in pairs]
def u_nested_target(triples):
    return [a + c for a, (b, c) in triples]
def u_star_target(pairs):
    return [a + rest[0] for a, *rest in pairs]
def u_dict_items(d):
    return [k * v for k, v in d.items()]
def u_two_star(pairs):
    return [[*a, *b] for a, b in pairs]
