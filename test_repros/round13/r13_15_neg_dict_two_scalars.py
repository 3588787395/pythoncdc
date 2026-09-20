# -*- coding: utf-8 -*-
"""R13 负对照 B：dict 字面量的值是**普通表达式**（非推导式），以及只有一个推导式值的 dict。

R13-D 只在「同一 dict 字面量里出现两个及以上推导式值」时触发，这里给出对照。
"""


def save_one_comp(open_orders, delayed_orders, dump):
    return {
        'open_orders': [dump(o) for o in open_orders],
        'delayed_orders': delayed_orders,
    }


def save_no_comp(a, b, c):
    return {
        'x': a + b,
        'y': c * 2,
        'z': [q for q in a],
    }


def nested_dict(v1, v2):
    return {'outer': {'inner_a': v1, 'inner_b': v2}}
