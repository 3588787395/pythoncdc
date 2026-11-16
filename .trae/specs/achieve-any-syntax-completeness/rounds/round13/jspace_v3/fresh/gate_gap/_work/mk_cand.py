#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write candidate probe sources for exploration (read-only experiments)."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "cand")
os.makedirs(OUT, exist_ok=True)

SRC = {
"c01_with_multi": '''
def outer(fa, fb):
    with fa() as a, fb() as b:
        x = a + b
    return x
''',
"c02_with_async": '''
async def outer(fa):
    async with fa() as a:
        y = await fb(a)
    return y
''',
"c03_elif_chain": '''
def outer(n):
    if n == 1:
        return 1
    elif n == 2:
        return 2
    elif n == 3:
        return 3
    elif n == 4:
        return 4
    else:
        return 5
''',
"c04_lambda_ifexp": '''
f = lambda x: x + 1 if x else 0
g = lambda y: (y * 2) if y > 1 else -y
''',
"c05_nested_def_if": '''
def outer(n):
    def inner(v):
        if v > 0:
            if v > 1:
                return v * 2
            elif v == 1:
                return 10
        elif v == 0:
            return 0
        return -1
    return inner(n)
''',
"c06_comp": '''
def outer(ns):
    a = [x * 2 for x in ns if x > 0]
    b = {k: v for k, v in zip(ns, ns)}
    c = {x + 1 for x in ns}
    d = (y - 1 for y in ns)
    return a, b, c, d
''',
"c07_match": '''
def outer(v):
    match v:
        case 1:
            r = 'one'
        case 2:
            r = 'two'
        case _:
            r = 'other'
    return r
''',
"c08_try_with": '''
def outer(fn):
    try:
        with fn() as h:
            return h.read()
    except ValueError:
        return None
    except (TypeError, KeyError) as e:
        raise
    finally:
        pass
''',
"c09_dict_ast": '''
def outer():
    d = {'a': 1, 'b': [2, 3]}
    d['c'] = d['a'] + 1
    return d
''',
"c10_del_import": '''
import os
import os.path as p
from sys import path

def outer():
    global _G
    x = 1
    del x
    assert x is None
    return p.join('a', 'b')
''',
"c11_with_nested": '''
def outer(fa, fb):
    with fa() as a:
        with fb() as b:
            return a + b
''',
"c12_async_with_multi": '''
async def outer(fa, fb, fc):
    async with fa() as a, fb() as b:
        s = await a
        t = await b
    return s, t
''',
"c13_yield_if": '''
def outer(ns):
    for n in ns:
        if n < 0:
            yield -n
        elif n == 0:
            yield 0
        else:
            yield n * 2
''',
"c14_class_if": '''
class Outer:
    def m(self, v):
        if v:
            return 1
        elif not v:
            return 2
        return 3
''',
}

for name, body in SRC.items():
    path = os.path.join(OUT, name + ".py")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("def _host():\n    pass\n\n" + body.lstrip())
print("wrote", len(SRC), "sources to", OUT)
