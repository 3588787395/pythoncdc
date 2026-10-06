#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 5（深层嵌套交叉矩阵对抗）探针程序化生成器。只写 test_repros/round5/r5v5_*.py 与 n5v5_*.py。

口径注记（前缀冲突处置）：
- test_repros/round5/ 已存在旧规范 round5 的已跟踪文件（r5_01..r5_13 / n5_01 / rv5_20..26），
  故本轮**不**复用 r5_*/n5_* 前缀（会覆盖 tracked 文件），改用轮次专属 r5v5_（攻击）/ n5v5_（负对照）。
- 宿主条件一律非常量，禁用 `if 1:` / `while 1:` + break（CPython 常量折叠伪差）。
- 覆盖空白格：Module 根 / ClassDef 体 / AnnAssign / f-string 转换符跨宿主 / keyword_args·star_args·
  walrus·slice 调用点 / decorator_with_args / for-else 跨宿主 / except* 深度外推 / Lambda 组合 /
  global-nonlocal 跨宿主 / elif·augassign 跨宿主。
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

PROBES = {}

# ─────────────────────────────────────────────────────────────────────────
# 空白格 ★组①  Module 根专攻（A1）
# ─────────────────────────────────────────────────────────────────────────
PROBES['r5v5_01_module_root'] = r'''
"""Round5 module root probe docstring（模块根 docstring 位）。"""
import os as _os
import os.path

MOD_A = 3
MOD_B: int = 5
MOD_C, MOD_D = 1, 2
MOD_E = MOD_F = 9
MOD_G = MOD_A if MOD_A > 0 else MOD_B


def m_root(x):
    return x + MOD_A


if MOD_A > 1:
    MOD_H = 'a'
elif MOD_A > 0:
    MOD_H = 'b'
else:
    MOD_H = 'c'

for _i in range(2):
    MOD_I = _i
else:
    MOD_I = -1

while MOD_D < 4:
    MOD_D += 1
else:
    MOD_D = 0

MOD_J = [v for v in range(3)]
MOD_K = f'{MOD_A!r}'

if __name__ == '__main__':
    MOD_L = MOD_A + MOD_B
'''

# ─────────────────────────────────────────────────────────────────────────
# 空白格 ★组②  ClassDef 体专攻（A15 组内）
# ─────────────────────────────────────────────────────────────────────────
PROBES['r5v5_02_class_body'] = r'''
class Doc:
    """class docstring here（类体 docstring 位）"""
    X = 1
    Y: int = 2
    Z: str
    W = X + Y

    class Inner:
        """inner class docstring"""
        I = 3
        J: int = 4

        class Inner2:
            K = 5

    def __init__(self, v):
        self.v = v
        self.a: int = 0

    def method(self, xs):
        r = 0
        for x in xs:
            if x > 0:
                r += x
            elif x < 0:
                r -= x
            else:
                r = 0
        self.a += r
        return f'{r!r}'

    @property
    def prop(self):
        return self.v


class Ctl:
    FLAG = 3
    if FLAG > 1:
        A = 1
        B = 2
    else:
        A = 0
        B = 0
    for _k in range(2):
        C = _k
    try:
        D = 1
    except Exception:
        D = 2
    with open('a') as f:
        E = f
    match FLAG:
        case 3:
            F = 'three'
        case _:
            F = 'other'
    G = [q for q in range(3)]
    H = f'{FLAG}'
'''

# ─────────────────────────────────────────────────────────────────────────
# 空白格 ★组③  AnnAssign（A12 组内）
# ─────────────────────────────────────────────────────────────────────────
PROBES['r5v5_03_annassign'] = r'''
MOD_AN: int = 0
MOD_AN2: 'list'
MOD_AN3: dict = {}


def ann_root(x):
    a: int = x + 1
    b: str
    c: dict = {}
    d: list = []
    return a, b, c, d


def ann_deep(x, xs):
    r = 0
    for i in xs:
        if i:
            a: int = i
            while a > 0:
                a -= 1
            r = a
    return r


class CAnn:
    cv: int = 5
    cv2: str

    def m(self, x, xs):
        a: int = x
        for i in xs:
            if i:
                b: int = i
        with open('a') as f:
            c: int = x
        try:
            d: int = x
        finally:
            pass
        match x:
            case 0:
                e: int = 1
            case _:
                e = 0
        return a, b, c, d, e


def ann_closure(x):
    c: int = 0

    def inc():
        nonlocal c
        c += 1
        return c
    return inc


def ann_nested3(x):
    def l1():
        def l2():
            def l3():
                z: int = x
                return z
            return l3()
        return l2()
    return l1()
'''

# ─────────────────────────────────────────────────────────────────────────
# 交叉：elif 链 × 类体/模块根/深宿主（7 族完备交叉复攻）
# ─────────────────────────────────────────────────────────────────────────
PROBES['r5v5_04_elif_cross'] = r'''
class EClass:
    S = 4
    if S == 1:
        V = 'a'
    elif S == 2:
        V = 'b'
    elif S == 3:
        V = 'c'
    elif S == 4:
        V = 'd'
    else:
        V = 'e'

    def m(self, x):
        for i in range(3):
            if x == i:
                r = 'a'
            elif x == i + 1:
                r = 'b'
            elif x == i + 2:
                r = 'c'
            else:
                r = 'd'
        return r


def efn_root(x):
    if x == 1:
        return 'a'
    elif x == 2:
        return 'b'
    elif x == 3:
        return 'c'
    return 'z'


def efn_deep(x, y, z):
    r = 0
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


_GE = 3
if _GE > 1:
    _GR = 'a'
elif _GE > 2:
    _GR = 'b'
elif _GE > 3:
    _GR = 'c'
else:
    _GR = 'd'
'''

# ─────────────────────────────────────────────────────────────────────────
# 交叉：augmented_assign × 类体/模块根/深宿主/闭包/global
# ─────────────────────────────────────────────────────────────────────────
PROBES['r5v5_05_augassign_cross'] = r'''
MOD_AA = 1
MOD_AA += 2
MOD_AA *= 3


def aug_root(x):
    y = x
    y += 1
    y //= 2
    y **= 2
    y &= 7
    return y


class CAug:
    CV = 1
    CV += 2

    def m(self, xs):
        for i in xs:
            if i:
                self.v += i
            elif i < 0:
                self.v -= i
            else:
                self.v = 0
        with open('a') as f:
            self.w += 1
        try:
            self.z += 1
        finally:
            self.z -= 1
        match xs:
            case []:
                self.q += 1
            case _:
                self.q -= 1
        return self.v


def aug_deep(x, xs):
    r = 0
    for i in xs:
        while i > 0:
            if i:
                r += i
                i -= 1
    return r


def aug_nonlocal(x):
    c = 0

    def inc():
        nonlocal c
        c += 1

    def outer():
        def inner():
            nonlocal c
            c += x
        inner()
    outer()
    return c


_GAA = 0


def aug_global():
    global _GAA
    _GAA += 1
    return _GAA
'''

# ─────────────────────────────────────────────────────────────────────────
# 空白格 ★组⑤  keyword_args 调用点（B6 组内）
# ─────────────────────────────────────────────────────────────────────────
PROBES['r5v5_06_keywordargs_callsite'] = r'''
MOD_KW = _kf(a=1, b=2)
MOD_KW2 = _kf(1, 2, k=3)


def kw_root(f):
    return f(a=1, b=2, c=3)


class CKw:
    V = _kf(k=1)

    def m(self, f):
        return f(self.v, key=self.w, other=2)


def kw_deep(f, g):
    r = 0
    for i in range(3):
        if i:
            r = f(alpha=i, beta=i + 1, gamma=i + 2)
    return r


def kw_nested(f, g):
    return f(g(a=1), b=g(c=2), d=3)


def kw_dict(f):
    return f(b=1, a=2, **{'c': 3})


def kw_closure(f):
    def inner():
        return f(x=1, y=2)
    return inner()


def kw_comp(f, xs):
    return [f(v=v, w=v + 1) for v in xs]


def kw_try(f):
    try:
        return f(a=1)
    finally:
        pass


def kw_match(f, x):
    match x:
        case 0:
            return f(a=1, b=2)
        case _:
            return f(a=0, b=0)


def kw_with(f):
    with open('a') as h:
        return f(a=len(h.name), b=2)
'''

# ─────────────────────────────────────────────────────────────────────────
# 空白格 ★组⑤  star_args 调用点（B6 组内）
# ─────────────────────────────────────────────────────────────────────────
PROBES['r5v5_07_starargs_callsite'] = r'''
def st_root(f, xs):
    return f(*xs)


def st_nontail(f, xs):
    return f(*xs, 1)


def st_mixed(f, xs):
    return f(1, *xs, 2, k=3)


def st_multistar(f, xs, ys):
    return f(*xs, *ys, **{'k': 0})


def st_deep(f, xs, ys):
    r = 0
    for i in range(2):
        if i:
            r = f(*xs, *ys, **{'k': i})
    return r


class CSt:
    def m(self, f, xs):
        for i in range(2):
            if i:
                return f(*xs, self.v)
        return f(*xs)


def st_close(f, xs):
    def inner():
        return f(*xs, *xs)
    return inner()


def st_match(f, xs, x):
    match x:
        case 0:
            return f(*xs)
        case _:
            return f(*xs, 1)


def st_comp(f, xs):
    return [f(*xs, v) for v in xs]
'''

# ─────────────────────────────────────────────────────────────────────────
# 空白格 ★组⑤  slice 调用点（C7 组内）
# ─────────────────────────────────────────────────────────────────────────
PROBES['r5v5_08_slice_callsite'] = r'''
def sl_root(s):
    return s[1:2]


def sl_nested(s):
    return s[1:2][0:1][::1]


def sl_call(s, g):
    return g(s[1:len(s) - 1:2], s[::-1])


def sl_deep(s, xs):
    r = 0
    for i in xs:
        if i:
            while i > 0:
                r = s[i:i + 2]
                i -= 1
    return r


class CSl:
    def m(self, s):
        with open('a') as f:
            return s[f.start:f.end:f.step]


def sl_comp(xs, n):
    return [x[n:] for x in xs]


def sl_target(xs):
    xs[1:3] = [0, 0]
    xs[:] = []
    del xs[::2]
    return xs


def sl_match(s, x):
    match x:
        case 0:
            return s[1:2]
        case _:
            return s[::2]
'''

# ─────────────────────────────────────────────────────────────────────────
# 空白格 ★组⑤  walrus 调用点（B9 组内）
# ─────────────────────────────────────────────────────────────────────────
PROBES['r5v5_09_walrus_callsite'] = r'''
def w_root(x):
    if (n := len(x)) > 3:
        return n
    return 0


def w_call(f, x):
    return f((n := x + 1), n)


def w_nested_call(f, g, x):
    return f((a := g(x)), (b := a + 1))


def w_deep(xs):
    r = 0
    for x in xs:
        while (m := x * 2) < 20:
            if m:
                r = m
            x += 1
    return r


class CW:
    def m(self, x):
        if (k := x + 1) > 0:
            return k
        return (j := x)


def w_comp(xs):
    return [y for x in xs if (y := x * 2) > 4]


def w_with(x):
    with open('a') as f:
        if (line := f.readline()) > '':
            return line
    return ''


def w_match(x):
    match x:
        case 0:
            return (n := x + 1)
        case _:
            return (m := x - 1)


def w_boolop(a, b):
    r = (x := a) and (y := b)
    return r
'''

# ─────────────────────────────────────────────────────────────────────────
# 空白格 ★组④  f-string 转换符 × 宿主交叉（B7/C9）
# ─────────────────────────────────────────────────────────────────────────
PROBES['r5v5_10_fstring_cross'] = r'''
MOD_FS = f'{MOD_A!r}'


def fs_root(x):
    return f'{x!r} {x!s} {x!a}'


class CFs:
    V = f'{1!r}'

    def m(self, x, w):
        if x:
            return f'a{x:>{w}}b'
        return f'{x!r:{w}}'


def fs_deep(d, n):
    r = ''
    for k in d:
        if k:
            for i in range(n):
                r = f'{d[k]!r:>{10}}'
    return r


def fs_nested_field(d):
    return f"{d['k']} = {d['k']!r}"


def fs_closure(x):
    def inner():
        return f'{x!a}'
    return inner()


def fs_comp(xs):
    return [f'{v!r}' for v in xs]


def fs_try(x):
    try:
        return f'{x!r}'
    finally:
        pass


def fs_with(x):
    with open('a') as f:
        return f'{x!r}{f.name!s}'


def fs_match(x):
    match x:
        case 0:
            return f'{x!r}'
        case _:
            return f'{x!s}'
'''

# ─────────────────────────────────────────────────────────────────────────
# 交叉：global / nonlocal × 宿主（A14）× 深度≥3
# ─────────────────────────────────────────────────────────────────────────
PROBES['r5v5_11_global_nonlocal_cross'] = r'''
_GNC = 0


def gn_root():
    global _GNC
    _GNC += 1
    return _GNC


class CGnc:
    def m(self):
        global _GNC
        _GNC -= 1
        return _GNC


def gn_deep():
    def mid():
        def inner():
            global _GNC
            _GNC = 9
        for i in range(2):
            if i:
                inner()
    mid()
    return _GNC


def gn_nonlocal_chain():
    c = 0

    def l1():
        def l2():
            def l3():
                nonlocal c
                c += 1
            l3()
        l2()
    l1()
    return c


def gn_both():
    global _GNC
    c = 0

    def inc():
        nonlocal c
        c += 1
    _GNC += c
    return _GNC


def gn_loop():
    global _GNC
    r = 0
    while _GNC < 5:
        _GNC += 1
        r = _GNC
    return r


def gn_match(x):
    global _GNC
    match x:
        case 0:
            _GNC += 1
        case _:
            _GNC -= 1
    return _GNC
'''

# ─────────────────────────────────────────────────────────────────────────
# 空白格 ★组⑥  decorator_with_args 交叉加深（C11）
# ─────────────────────────────────────────────────────────────────────────
PROBES['r5v5_12_decorator_cross'] = r'''
def deco(n):
    def wrap(f):
        def inner(*a, **k):
            return f(*a, **k)
        return inner
    return wrap


@deco(1)
def d_root(x):
    return x


@deco(2)
class DClass:
    @deco(3)
    def m(self, x):
        return x

    @deco(4)
    @staticmethod
    def s(x):
        return x

    @deco(5)
    @property
    def p(self):
        return self.v


def d_deep(x):
    class Local:
        @deco(x)
        def m(self):
            return x
    return Local


def d_closure(x):
    def outer():
        @deco(x)
        def inner():
            return x
        return inner
    return outer()


def d_stack(x):
    @deco(x)
    @deco(x + 1)
    @deco(x + 2)
    def inner():
        return x
    return inner


def d_nested_deco():
    @deco(deco(1)(lambda y: y)(2))
    def inner():
        return 0
    return inner


def d_async():
    @deco(6)
    async def inner():
        return 1
    return inner
'''

# ─────────────────────────────────────────────────────────────────────────
# 交叉：for-else / while-else × 宿主（C2）× 深度≥3
# ─────────────────────────────────────────────────────────────────────────
PROBES['r5v5_13_for_else_cross'] = r'''
MOD_FE = 0
for _q in range(3):
    if _q > 1:
        break
else:
    MOD_FE = -1


def fe_root(xs):
    for x in xs:
        if x > 10:
            break
    else:
        return 'none'
    return x


class CFe:
    def m(self, xs):
        while xs:
            y = xs.pop()
            if y > 3:
                break
        else:
            return None
        return y


def fe_deep(xs, ys):
    r = 0
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


def fe_try(xs):
    try:
        for x in xs:
            if x:
                break
        else:
            r = -1
    finally:
        pass
    return r


def fe_with(xs):
    with open('a') as f:
        for x in xs:
            if x == f.name:
                break
        else:
            r = 0
    return r


def fe_match(xs, n):
    match n:
        case 0:
            for x in xs:
                r = x
            else:
                r = -1
        case _:
            r = 1
    return r


def fe_closure(xs):
    def inner():
        for x in xs:
            if x > 1:
                break
        else:
            return 0
        return x
    return inner()


def fe_while_deep(n, m):
    i = 0
    while i < n:
        j = 0
        while j < m:
            if j > 2:
                break
            j += 1
        else:
            i = n
        i += 1
    else:
        return -1
    return i
'''

# ─────────────────────────────────────────────────────────────────────────
# 次级空白：except* / TryStar 深度外推（A7/C3）
# ─────────────────────────────────────────────────────────────────────────
PROBES['r5v5_14_except_star_deep'] = r'''
def es_root(fn):
    r = None
    try:
        fn()
    except* ValueError as eg:
        r = eg.exceptions
    except* TypeError as eg:
        r = eg.exceptions
    return r


def es_deep(fn):
    for i in range(2):
        if i:
            try:
                fn()
            except* ValueError as eg:
                _h(eg)
            except* TypeError as eg:
                _h(eg)
    return i


class CEs:
    def m(self, fn):
        while _cond():
            try:
                fn()
            except* RuntimeError as eg:
                _h(eg)


def es_with(fn):
    with _ctx() as c:
        try:
            fn()
        except* KeyError as eg:
            _h(eg)
        else:
            _ok()
        finally:
            _done()
    return c


def es_nested(fn):
    try:
        try:
            fn()
        except* ValueError as eg:
            _h(eg)
    except* TypeError as eg:
        _h(eg)
    return 0


def es_match(fn, x):
    match x:
        case 0:
            try:
                fn()
            except* ValueError as eg:
                _h(eg)
        case _:
            pass
    return 0


def es_closure(fn):
    def inner():
        r = None
        try:
            fn()
        except* Exception as eg:
            r = eg.exceptions
        return r
    return inner()
'''

# ─────────────────────────────────────────────────────────────────────────
# 次级空白：Lambda 组合加深（B4）
# ─────────────────────────────────────────────────────────────────────────
PROBES['r5v5_15_lambda_combo'] = r'''
def lam_root(x):
    f = lambda a: a + x
    return f


class CLam:
    V = 1
    f = lambda self: self.V

    def m(self, xs):
        g = lambda a, b=2: a + b
        return [g(v) for v in xs]


def lam_default(x):
    return lambda a, b=x, *args, **kw: a + b


def lam_comp(xs):
    return [(lambda v: v * 2)(x) for x in xs]


def lam_deep(x, ys):
    return [[(lambda a: a + y)(x) for y in ys] for _ in range(2)]


def lam_star(xs):
    f = lambda *a: a
    return f(*xs)


def lam_boolop(a, b):
    f = lambda: (a or b) and a
    return f


def lam_nested(x):
    f = lambda y: (lambda z: z + y)(x)
    return f


def lam_closure(x):
    def outer():
        return lambda: x + 1
    return outer()
'''

# ─────────────────────────────────────────────────────────────────────────
# 负对照（浅层、单一形态；MATCH 对照组）
# ─────────────────────────────────────────────────────────────────────────
PROBES['n5v5_01_module_class_shallow'] = r'''
"""neg module docstring."""


def n_root(x):
    return x + 1


class NClass:
    """neg class docstring."""
    V = 1
    W: int = 2

    def m(self):
        return self.V
'''

PROBES['n5v5_02_callsite_shallow'] = r'''
def n_kw(f):
    return f(a=1, b=2)


def n_star(f, xs):
    return f(*xs)


def n_slice(s):
    return s[1:2]


def n_walrus(x):
    return (n := x)
'''

PROBES['n5v5_03_fstring_deco_shallow'] = r'''
def deco(n):
    def wrap(f):
        return f
    return wrap


@deco(1)
def n_deco(x):
    return x


def n_fstring(x):
    return f'{x!r}'


def n_deco_class():
    @deco(2)
    class C:
        pass
    return C
'''

PROBES['n5v5_04_control_shallow'] = r'''
def n_elif(x):
    if x == 1:
        return 'a'
    elif x == 2:
        return 'b'
    return 'c'


def n_for_else(xs):
    for x in xs:
        r = x
    else:
        r = 0
    return r


def n_aug(x):
    y = x
    y += 1
    return y


def n_global():
    global _NG
    _NG = 1
    return _NG


def n_ann(x):
    a: int = x
    return a
'''


def main():
    names = []
    for name, src in PROBES.items():
        path = os.path.join(HERE, name + '.py')
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(src.lstrip('\n'))
        names.append(name)
        print('wrote', name + '.py', len(src.splitlines()), 'lines')
    print('total', len(names), 'probe files')


if __name__ == '__main__':
    main()