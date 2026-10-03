# Source Generated with Decompyle++ (Python version)
# File: r7_02_ternary_containers.pyc (Python 3.11)

__doc__ = 'R7-02 三元容器元素位置面（dict 键/值、list、set、tuple）。'
def t_dict_value(k, flag, v1, v2):
    return {k: v1 if flag else v2}
def t_dict_key_ternary(k1, k2, v, flag):
    return {k1 if flag else k2: v}
def t_dict_both_ternary(k1, k2, v1, v2, c1, c2):
    return {k1 if c1 else k2: v1 if c2 else v2}
def t_list_element(a, b, flag):
    return [a, b if flag else a, a if flag else b]
def t_set_element(a, b, flag):
    return {a if flag else b, b}
def t_tuple_element(a, b, flag):
    return (a if flag else b, b if flag else a)
def t_nested_container(xs, flag):
    return {'k': [xs[0] if flag else xs[-1], {1 if flag else 2}]}
