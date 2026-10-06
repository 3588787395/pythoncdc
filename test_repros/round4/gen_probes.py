#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 4（表C 31 扩展形态对抗）探针程序化生成器。只写 test_repros/round4/*.py。

设计纪律：
- 每形态 ≥10 个深层/交叉复现（嵌套深度尽量 ≥3），宿主矩阵交叉
  （模块根/类体/函数根/if/for/while/try/with/match/推导式/嵌套闭包）。
- 宿主条件禁用字面常量（`if 1:`/`while 1:` 会被 CPython 常量折叠产生伪差）。
- 新探针前缀 c4（攻击）/ n4（负对照），零覆盖 round3 的 e*/n*/r3* 文件。
- c4 攻击文件同时内嵌浅层对照函数（同名 _shallow 后缀），n4 为纯浅层负对照。
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

PROBES = {}

# ─────────────────────────────────────────────────────────────────────────
# 族 1  elif 链
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_01_elif_chain'] = r'''
def e01_root(x):
    if x == 1:
        return 'a'
    elif x == 2:
        return 'b'
    elif x == 3:
        return 'c'
    elif x == 4:
        return 'd'
    else:
        return 'e'


def e02_shallow(x):
    if x == 1:
        return 'a'
    elif x == 2:
        return 'b'
    return 'c'


def e03_nested_if(x, y):
    if y > 0:
        if x == 1:
            r = 1
        elif x == 2:
            r = 2
        elif x == 3:
            r = 3
        else:
            r = 4
    else:
        if x == 1:
            r = 5
        elif x == 2:
            r = 6
        else:
            r = 7
    return r


class CE:
    def m(self, x):
        for i in range(3):
            if x == i:
                v = 'a'
            elif x == i + 1:
                v = 'b'
            elif x == i + 2:
                v = 'c'
            else:
                v = 'd'
        return v


def e04_deep(x, y, z):
    while x > 0:
        if y > 0:
            if z == 1:
                r = 1
            elif z == 2:
                r = 2
            else:
                r = 3
        elif y < 0:
            if z == 1:
                r = 4
            elif z == 2:
                r = 5
            else:
                r = 6
        else:
            r = 7
        x -= 1
    return r


def e05_try_host(x):
    try:
        if x == 1:
            r = 'a'
        elif x == 2:
            r = 'b'
        elif x == 3:
            r = 'c'
        else:
            r = 'd'
    finally:
        r = r
    return r


def e06_with_host(x):
    with open('t') as f:
        if x == 1:
            r = 1
        elif x == 2:
            r = 2
        elif x == 3:
            r = 3
        else:
            r = 4
    return r


def e07_match_host(x):
    match x:
        case 0:
            if x == 1:
                r = 1
            elif x == 2:
                r = 2
            elif x == 3:
                r = 3
            else:
                r = 4
        case _:
            r = 0
    return r


def e08_closure_host(x):
    def inner():
        if x == 1:
            return 1
        elif x == 2:
            return 2
        elif x == 3:
            return 3
        return 4
    return inner()


def e09_comp_host(xs):
    return [1 if x == 1 else (2 if x == 2 else (3 if x == 3 else 0)) for x in xs]


_G = 3
if _G > 1:
    _r = 'a'
elif _G > 2:
    _r = 'b'
elif _G > 3:
    _r = 'c'
else:
    _r = 'd'
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 2  for-else / while-else
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_02_loop_else'] = r'''
def e01_for_else(xs):
    for x in xs:
        if x > 10:
            break
    else:
        return 'none'
    return x


def e02_while_else(n):
    i = 0
    while i < n:
        if i == 5:
            break
        i += 1
    else:
        return -1
    return i


def e03_shallow_for(xs):
    for x in xs:
        r = x
    else:
        r = 0
    return r


def e04_deep(xs, ys):
    for x in xs:
        if x > 0:
            for y in ys:
                if y > x:
                    r = y
                    break
            else:
                r = x
        else:
            r = 0
    return r


def e05_try_host(xs):
    try:
        for x in xs:
            if x:
                r = x
                break
        else:
            r = -1
    finally:
        pass
    return r


def e06_with_host(xs):
    with open('a') as f:
        for x in xs:
            if x == f:
                break
        else:
            r = 0
    return r


def e07_match_host(xs):
    match len(xs):
        case 0:
            for x in xs:
                r = x
            else:
                r = -1
        case _:
            r = 1
    return r


class CL:
    def m(self, xs):
        while xs:
            y = xs.pop()
            if y > 3:
                break
        else:
            return None
        return y


def e08_closure(xs):
    def inner():
        for x in xs:
            if x > 1:
                break
        else:
            return 0
        return x
    return inner()


def e09_comp_host(xs):
    return [x for x in xs if (x > 1 or x < -1)]
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 3  except* 异常组（3.11 标记 CHECK_EG_MATCH / PREP_RERAISE_STAR）
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_03_except_star'] = r'''
def e01_root(fn):
    r = None
    try:
        fn()
    except* ValueError as eg:
        r = eg.exceptions
    except* TypeError as eg:
        r = eg.exceptions
    return r


def e02_shallow(fn):
    r = None
    try:
        fn()
    except* KeyError as eg:
        r = eg
    return r


def e03_deep(fn):
    for i in range(2):
        if i:
            try:
                fn()
            except* ValueError as eg:
                handle(eg)
            except* TypeError as eg:
                handle(eg)
    return i


def e04_with(fn):
    with ctx() as c:
        try:
            fn()
        except* KeyError as eg:
            handle(eg)
        else:
            ok()
        finally:
            done()
    return c


def e05_nested(fn):
    try:
        try:
            fn()
        except* ValueError as eg:
            handle(eg)
    except* TypeError as eg:
        handle(eg)
    return 0


def e06_while(fn):
    n = 0
    while n < 3:
        try:
            fn()
        except* OSError as eg:
            for e in eg.exceptions:
                handle(e)
        n += 1
    return n


class CX:
    def m(self, fn):
        while cond():
            try:
                fn()
            except* RuntimeError as eg:
                handle(eg)


def e07_closure(fn):
    def inner():
        r = None
        try:
            fn()
        except* Exception as eg:
            r = eg.exceptions
        return r
    return inner()


def e08_match_host(fn):
    match flag():
        case 0:
            try:
                fn()
            except* ValueError as eg:
                handle(eg)
        case _:
            pass
    return 0


def e09_if_else(fn):
    if flag():
        try:
            fn()
        except* ValueError as eg:
            handle(eg)
    else:
        try:
            fn()
        except* TypeError as eg:
            handle(eg)
    return 0
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 4  match + 守卫 + 8 模式
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_04_match_patterns'] = r'''
def e01_value(x):
    if x > 0:
        match x:
            case 1:
                r = 'one'
            case 2:
                r = 'two'
            case 3 | 4:
                r = 'few'
            case _:
                r = 'many'
    else:
        r = 'neg'
    return r


def e02_singleton(x):
    for i in range(3):
        match x:
            case None:
                r = 0
            case True:
                r = 1
            case False:
                r = 2
            case object():
                r = 3
    return r


def e03_sequence(x, y, z):
    if x:
        match y:
            case [a, b, c]:
                r = a + b + c
            case [a, *rest]:
                r = a
            case (a, b):
                r = a - b
            case _:
                r = 0
    return r


def e04_mapping(x):
    while x:
        match x:
            case {'a': 1, 'b': b}:
                r = b
            case {'k': v, **rest}:
                r = v
            case _:
                r = 0
    return r


def e05_class_kw(x):
    try:
        match x:
            case Point(x=0, y=0):
                r = 'origin'
            case Point(x=px, y=py):
                r = px + py
            case _:
                r = 0
    finally:
        pass
    return r


def e06_or_guard(x):
    with ctx():
        match x:
            case 1 | 2 | 3 if x > 1:
                r = 'small'
            case 4 | 5 if x > 4:
                r = 'mid'
            case _:
                r = 'other'
    return r


def e07_capture(x, y):
    def inner():
        match x:
            case [a, b] if a > b:
                return a
            case [a, b]:
                return b
            case a if a is not None:
                return a
            case _:
                return 0
    return inner()


def e08_star_nest(x):
    match x:
        case [1, *mid, 9]:
            r = mid
        case {'key': [first, *rest]}:
            r = first
        case (head, *tail):
            r = tail
        case _:
            r = None
    return r


def e09_nested_match(x, y):
    match x:
        case [a, b]:
            match a:
                case 1:
                    r = 'a1'
                case _:
                    r = 'ax'
        case _:
            match y:
                case 2:
                    r = 'y2'
                case _:
                    r = 'yx'
    return r


class CM:
    def m(self, x):
        match x:
            case {'a': v} if v:
                return v
            case [*items]:
                return items
            case _:
                return None
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 5  多上下文 with
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_05_multi_with'] = r'''
def e01_root(a, b):
    with open(a) as f, open(b) as g:
        return f.read() + g.read()


def e02_shallow(a):
    with open(a) as f:
        return f.read()


def e03_triple(a, b, c):
    with open(a) as f, open(b) as g, open(c) as h:
        return f.read() + g.read() + h.read()


def e04_deep(x, a, b):
    if x:
        for i in range(2):
            with open(a) as f, open(b) as g:
                r = f.read() + g.read() + str(i)
    return r


def e05_try_host(a, b):
    try:
        with open(a) as f, open(b) as g:
            r = f.read() + g.read()
    finally:
        pass
    return r


def e06_while_host(a, b):
    i = 0
    while i < 3:
        with open(a) as f, open(b) as g:
            r = f.read() + g.read()
        i += 1
    return r


class CW:
    def m(self, a, b):
        with open(a) as f, open(b) as g:
            with open('c') as h, open('d') as k:
                return f.read() + g.read() + h.read() + k.read()


def e07_match_host(a, b):
    match flag():
        case 0:
            with open(a) as f, open(b) as g:
                r = f.read() + g.read()
        case _:
            r = None
    return r


def e08_closure(a, b):
    def inner():
        with open(a) as f, open(b) as g:
            return f.read() + g.read()
    return inner()


def e09_comp_host(a, b):
    return [(f, g) for f in [open(a)] for g in [open(b)]]
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 6  try-finally-only
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_06_try_finally_only'] = r'''
def e01_root(x):
    try:
        r = x + 1
    finally:
        r = r if r else 0
    return r


def e02_shallow(x):
    try:
        r = x
    finally:
        log(r)
    return r


def e03_deep(x):
    for i in range(3):
        if i:
            try:
                r = x + i
            finally:
                log(r)
    return r


def e04_nested(x):
    try:
        try:
            r = x
        finally:
            a = 1
    finally:
        b = 2
    return r


def e05_with(x):
    with open('a') as f:
        try:
            r = f.read()
        finally:
            f.close()
    return r


def e06_while(x):
    n = 0
    while n < 3:
        try:
            r = x + n
        finally:
            del x
        n += 1
    return r


class CF:
    def m(self, x):
        try:
            self.v = x
        finally:
            self.v = 0
        return self.v


def e07_match_host(x):
    match x:
        case 0:
            try:
                r = 1
            finally:
                r = 2
        case _:
            r = 0
    return r


def e08_closure(x):
    def inner():
        try:
            return x
        finally:
            log(x)
    return inner()


def e09_comp_host(xs):
    return [x for x in xs if x]
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 7  multi_target_assign
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_07_multi_target'] = r'''
def e01_root(x):
    a = b = c = x + 1
    return a + b + c


def e02_shallow(x):
    a = b = x
    return a + b


def e03_deep(x):
    p = 0
    for i in range(3):
        if i:
            p = q = r = i * 2
    return p + q + r


def e04_unpack(x):
    a, b = c, d = (x, x + 1)
    return a + b + c + d


def e05_star_unpack(x):
    a, *b = c, *d = [x, x + 1, x + 2]
    return a, b, c, d


def e06_chain_target(x):
    a = b = [x, x]
    a[0] = b[1] = x + 1
    return a[0] + b[1]


class CMT:
    def m(self, x):
        with open('a') as f:
            p = q = f.read()
        return p + q


def e07_match_host(x):
    match x:
        case 0:
            a = b = x + 1
        case _:
            a = b = 0
    return a + b


def e08_closure(x):
    def inner():
        a = b = x
        return a + b
    return inner()


def e09_attr_chain(x):
    class O:
        pass
    o = O()
    o.a = o.b = x
    return o.a + o.b
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 8  augmented_assign
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_08_augassign'] = r'''
def e01_root(x):
    y = x
    y += 1
    y -= 2
    y *= 3
    y //= 2
    y %= 5
    y **= 2
    return y


def e02_bit(x):
    y = x
    y &= 7
    y |= 8
    y ^= 3
    y <<= 1
    y >>= 2
    return y


def e03_deep(x, xs):
    for i in range(3):
        if i:
            xs[0] += i
            xs[1] -= i
    return xs


def e04_boolop_rhs(x, a, b):
    r = x
    r += (a or b)
    return r


def e05_attr(obj):
    obj.v += 1
    obj.v *= 2
    return obj.v


def e06_matmul(M, N):
    M @= N
    return M


def e07_b76_deep(x, a, b):
    r = x
    for i in range(2):
        if i:
            r += (a and b) or a
    return r


class CAU:
    def m(self, x):
        self.v = x
        self.v += 1
        self.v //= 2
        return self.v


def e08_shallow(x):
    y = x
    y += 1
    return y


def e09_close(x):
    c = 0

    def inc():
        nonlocal c
        c += 1
        return c
    return inc
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 9  chained_comparison
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_09_chained_compare'] = r'''
def e01_root(a, b, c):
    return a < b < c


def e02_shallow(a, b):
    return a < b


def e03_mixed(a, b, c, d):
    if a < b <= c != d:
        return 1
    return 0


def e04_deep(xs):
    for x in xs:
        if 0 < x < 10 < x * 2:
            r = x
        else:
            r = 0
    return r


def e05_is_in(a, b, c):
    return a is b is not c


def e06_notin(a, b, c):
    return a in b not in c


def e07_comp(xs):
    return [x for x in xs if 0 < x < 100]


def e08_while(x):
    n = 0
    while 0 < x < n < 100:
        n += 1
    return n


class CCMP:
    def m(self, a, b, c):
        with open('a') as f:
            return a < b < c < len(f.read())


def e09_closure(a, b, c):
    def inner():
        return a < b < c
    return inner()
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 10  walrus (NamedExpr)
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_10_walrus'] = r'''
def e01_root(x):
    if (n := len(x)) > 3:
        return n
    return 0


def e02_shallow(x):
    return (n := len(x))


def e03_while(xs):
    i = 0
    while (v := xs[i]) < 10:
        i += 1
    return v


def e04_comp(xs):
    return [y for x in xs if (y := x * 2) > 4]


def e05_nested(x, y):
    r = 0
    if x:
        if (a := x + 1) > y:
            r = a
        elif (b := x - 1) > y:
            r = b
        else:
            r = 0
    return r


def e06_call_arg(x, f):
    return f((n := x + 1), n)


def e07_in_boolop(a, b):
    r = (x := a) and (y := b)
    return r


def e08_deep(xs):
    for x in xs:
        while (m := x * 2) < 20:
            x = x + 1
    return m


class CW2:
    def m(self, x):
        if (k := x + 1) > 0:
            return k
        return 0


def e09_with(x):
    with open('a') as f:
        if (line := f.readline()) > '':
            return line
    return ''
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 11  keyword_args
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_11_keyword_args'] = r'''
def e01_root(f):
    return f(1, 2, key=3, other=4)


def e02_shallow(f):
    return f(key=1)


def e03_deep(f):
    r = 0
    for i in range(3):
        if i:
            r = f(a=i, b=i + 1, c=i + 2)
    return r


def e04_dup_order(f):
    return f(b=1, a=2, **{'c': 3})


def e05_mixed_pos(f):
    return f(1, 2, x=3, y=4)


class CKA:
    def m(self, f):
        return f(self.v, key=self.w)


def e06_match_host(f):
    match flag():
        case 0:
            r = f(a=1, b=2)
        case _:
            r = f(a=0, b=0)
    return r


def e07_closure(f):
    def inner():
        return f(alpha=1, beta=2, gamma=3)
    return inner()


def e08_comp(f):
    return [f(v=v) for v in range(3)]


def e09_nested_call(f, g):
    return f(g(a=1), b=g(c=2), d=3)
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 12  star_args
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_12_star_args'] = r'''
def e01_root(f, xs):
    return f(*xs)


def e02_shallow(f, x):
    return f(*x, 1)


def e03_mixed(f, xs):
    return f(1, *xs, 2, key=3)


def e04_deep(f, xs, ys):
    r = 0
    for i in range(2):
        if i:
            r = f(*xs, *ys, **{'k': i})
    return r


def e05_defn(*args, **kwargs):
    return args, kwargs


def e06_nested(f, xs):
    def inner():
        return f(*xs, *xs)
    return inner()


class CSA:
    def m(self, f, xs):
        return f(*xs, self.v)


def e07_match_host(f, xs):
    match flag():
        case 0:
            r = f(*xs)
        case _:
            r = f(*xs, 1)
    return r


def e08_kwstar(f, d):
    return f(**d)


def e09_mixed_all(f, xs, d):
    return f(1, *xs, k=2, **d)
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 13  slice
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_13_slice'] = r'''
def e01_root(s):
    return s[1:2]


def e02_shallow(s):
    return s[:]


def e03_step(s):
    return s[::2]


def e04_deep(s):
    if s:
        return s[1:len(s) - 1:2]
    return s[::-1]


def e05_tuple(s, t):
    return (s, t)[0][1:2]


def e06_target(xs):
    xs[1:3] = [0, 0]
    xs[:] = []
    del xs[::2]
    return xs


class CSL:
    def m(self, s):
        with open('a') as f:
            return s[f.start:f.end:f.step]


def e07_expr_bounds(s, a, b, c):
    return s[a + 1:b - 1:c * 2]


def e08_comp(xs, n):
    return [x[n:] for x in xs]


def e09_nested(s):
    return s[1:2][0:1][::1]
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 14  relative_import
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_14_relative_import'] = r'''
from . import mod
from .sub import name as n2
from ..pkg import other as o2


def e01_use():
    return mod, n2, o2


def e02_deep():
    r = 0
    for i in range(2):
        if i:
            r = mod.attr
    return r


class CRI:
    def m(self):
        return n2


_G = mod
if _G is not None:
    _x = n2
else:
    _x = o2
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 15  star_import
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_15_star_import'] = r'''
from os.path import *
from collections import *


def e01_use():
    return join, path


def e02_deep(x):
    r = 0
    for i in range(2):
        if i:
            r = join(x, str(i))
    return r


class CSI:
    def m(self):
        return path


def e03_comp(xs):
    return [join(x, 'a') for x in xs]


_G = path
if _G is not None:
    _y = join
else:
    _y = None
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 16  global / nonlocal
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_16_global_nonlocal'] = r'''
_G = 0


def e01_global():
    global _G
    _G += 1
    return _G


def e02_shallow():
    global _G
    _G = 1
    return _G


def e03_deep():
    def inner():
        global _G
        _G += 2
        return _G
    r = 0
    for i in range(2):
        if i:
            r = inner()
    return r


def make():
    c = 0

    def inc():
        nonlocal c
        c += 1
        return c
    return inc


class CG:
    def m(self):
        global _G
        _G -= 1
        return _G


def e04_nonlocal_deep():
    c = 0

    def outer():
        def inner2():
            nonlocal c
            c += 10
        for i in range(2):
            if i:
                inner2()
    outer()
    return c


def e05_global_in_loop():
    global _G
    r = 0
    while _G < 5:
        _G += 1
        r = _G
    return r


def e06_both():
    global _G
    c = 0

    def inc():
        nonlocal c
        c += 1
    _G += c
    return _G


def e07_nested_global():
    def mid():
        def inner():
            global _G
            _G = 9
        inner()
    mid()
    return _G


def e08_nonlocal_comp():
    c = 0

    def bump(xs):
        nonlocal c
        for x in xs:
            c += x
    bump([1, 2])
    return c


def e09_global_cond():
    global _G
    if _G > 0:
        _G += 1
    else:
        _G -= 1
    return _G
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 17  fstring_conversion
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_17_fstring_conv'] = r'''
def e01_root(x):
    return f'{x!r} {x!s} {x!a}'


def e02_shallow(x):
    return f'{x!r}'


def e03_nested(x, w):
    if x:
        return f'a{x:>{w}}b'
    return f'{x!r:{w}}'


def e04_deep(d):
    r = ''
    for k in d:
        if k:
            r = f'{d[k]!r:>{10}}'
    return r


def e05_nested_field(d):
    return f"{d['k']} = {d[ 'k' ]!r}"


def e06_format_spec(x, y):
    return f'{x:{y}}'


def e07_multi(a, b):
    return f'{a}{b!r}{a!s}'


class CFS:
    def m(self, x):
        return f'self={x!r}'


def e08_deep_field(d, n):
    r = ''
    for i in range(n):
        if i:
            r = f'{d[i]!r:{i}}'
    return r


def e09_conversion_expr(x):
    return f'{(x + 1)!r} {(x * 2)!s}'
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 18  nested_comprehension
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_18_nested_comprehension'] = r'''
def e01_root(xs):
    return [[y for y in x] for x in xs]


def e02_shallow(xs):
    return [y for y in xs]


def e03_dict(xs, ys):
    return {x: [y for y in ys if y > x] for x in xs}


def e04_gen(xs):
    return list((y for x in xs for y in x))


def e05_deep_host(xs):
    r = None
    for x in xs:
        if x:
            r = {a: {b for b in x} for a in xs}
    return r


def e06_triple(xs):
    return [[[z for z in y] for y in x] for x in xs]


def e07_cond_nest(xs):
    return [y for x in xs if x for y in x if y]


class CNC:
    def m(self, xs):
        with open('a') as f:
            return [(x, f) for x in xs if x]


def e08_set(xs):
    return {frozenset(y for y in x) for x in xs}


def e09_closure(xs):
    def inner():
        return {k: [v for v in x] for k, x in enumerate(xs)}
    return inner()
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 19  decorator_with_args
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_19_decorator_args'] = r'''
def deco(n):
    def wrap(f):
        def inner(*a, **k):
            return f(*a, **k)
        return inner
    return wrap


@deco(1)
def e01(x):
    return x


@deco(2)
@deco(3)
def e02(x):
    return x + 1


class CD:
    @deco(4)
    def m(self, x):
        return x


def e03_shallow(x):
    return x


def e04_deep(f):
    @deco(f(1))
    def inner():
        return 1
    return inner


def e05_closure(x):
    def outer():
        @deco(x)
        def inner():
            return x
        return inner
    return outer()


def e06_nested_deco():
    @deco(deco(1)(lambda y: y)(2))
    def inner():
        return 0
    return inner


class CD2:
    @deco(5)
    @staticmethod
    def s(x):
        return x

    @deco(6)
    @property
    def p(self):
        return self.v


@deco(7)
class CD3:
    pass


def e07_stack(x):
    @deco(x)
    @deco(x + 1)
    @deco(x + 2)
    def inner():
        return x
    return inner


def e08_async():
    @deco(8)
    async def inner():
        return 1
    return inner


def e09_method_local(x):
    class Local:
        @deco(x)
        def m(self):
            return x
    return Local
'''

# ─────────────────────────────────────────────────────────────────────────
# 族 20  async 五件套 + yield from
# ─────────────────────────────────────────────────────────────────────────
PROBES['c4_20_async_five'] = r'''
def sync_gen(n):
    yield n
    yield from range(n)


def e01_await(x):
    async def go():
        return await x
    return go


def e02_async_for(gen):
    async def go():
        async for v in gen:
            yield v
    return go


def e03_async_with(ctx):
    async def go():
        async with ctx as c:
            return c
    return go


def e04_await_deep(x, ys):
    async def go():
        r = 0
        for y in ys:
            if y:
                r = await x + await x
        return r
    return go


def e05_async_compound(gen):
    async def go():
        async for v in gen:
            async with v as c:
                yield await c
    return go


def e06_async_deep(gen):
    async def go():
        if gen:
            async for v in gen:
                await v
        return 0
    return go


class CAA:
    async def m(self, ctx):
        async with ctx as c:
            return await c


def e07_async_closure(gen):
    def outer():
        async def inner():
            return [v async for v in gen]
        return inner
    return outer


def e08_yield_from(n):
    def go():
        yield from range(n)
        yield from sync_gen(n)
    return go


def e09_async_await_yieldfrom(gen):
    async def go():
        r = 0
        async for v in gen:
            r = await v
        return r
    return go
'''

# ─────────────────────────────────────────────────────────────────────────
# 负对照（浅层、单一形态；MATCH 对照组）
# ─────────────────────────────────────────────────────────────────────────
PROBES['n4_01_neg_control_flow'] = r'''
def n_for_else(xs):
    for x in xs:
        r = x
    else:
        r = 0
    return r


def n_while_else(n):
    i = 0
    while i < n:
        i += 1
    else:
        return i
    return i


def n_elif(x):
    if x == 1:
        return 'a'
    elif x == 2:
        return 'b'
    return 'c'


def n_try_finally(x):
    try:
        r = x
    finally:
        r = x
    return r
'''

PROBES['n4_02_neg_expr'] = r'''
def n_multi_target(x):
    a = b = x
    return a + b


def n_augassign(x):
    y = x
    y += 1
    return y


def n_chain_compare(a, b, c):
    return a < b < c


def n_walrus(x):
    return (n := x)


def n_slice(s):
    return s[1:2]


def n_fstring(x):
    return f'{x!r}'


def n_kwarg(f):
    return f(a=1, b=2)


def n_star(f, xs):
    return f(*xs)


def n_nested_comp(xs):
    return [[y for y in x] for x in xs]
'''

PROBES['n4_03_neg_match_with'] = r'''
def n_match_value(x):
    match x:
        case 1:
            return 'one'
        case _:
            return 'other'


def n_match_seq(x):
    match x:
        case [a, b]:
            return a + b
        case _:
            return 0


def n_multi_with(a, b):
    with open(a) as f, open(b) as g:
        return f.read() + g.read()


def n_global():
    global _NEG
    _NEG = 1
    return _NEG
'''

PROBES['n4_04_neg_deco_async'] = r'''
def deco(n):
    def wrap(f):
        return f
    return wrap


@deco(1)
def n_deco(x):
    return x


async def n_await(x):
    return await x


async def n_async_for(gen):
    async for v in gen:
        yield v


async def n_async_with(ctx):
    async with ctx as c:
        return c


def n_yield_from(n):
    yield from range(n)
'''

PROBES['n4_05_neg_except_star'] = r'''
def n_except_star(fn):
    r = None
    try:
        fn()
    except* ValueError as eg:
        r = eg.exceptions
    return r


def n_except_star_two(fn):
    try:
        fn()
    except* ValueError as eg:
        handle(eg)
    except* TypeError as eg:
        handle(eg)
    return None
'''


def main():
    for name, src in PROBES.items():
        path = os.path.join(HERE, name + '.py')
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(src.lstrip('\n'))
        print('wrote', name + '.py', len(src.splitlines()), 'lines')
    print('total', len(PROBES), 'probe files')


if __name__ == '__main__':
    main()