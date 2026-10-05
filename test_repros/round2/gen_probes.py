#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 2 adversarial probe generator - Table A statement-structure forms.

Group 1 (Module root, A1): m01-m12 probes + nm01/nm02 negative controls.
Group 2 (ClassDef body, A15): c01-c15 probes + nc01/nc02 negative controls.
Group 3 (cross-host depth>=3): x01-x10 probes + nx01 negative control.

Writes probe .py files next to this script. ASCII only.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

PROBES = {}

# ---------------------------------------------------------------- Group 1: Module

PROBES['m01_docstring_order.py'] = '''\
"""m01: module docstring position and statement order at root."""
MOD_CONST = 1
import os as _os
import sys
from collections import OrderedDict as _OD

_MX = _os.name
MOD_SECOND = 'second'


def _f():
    if _MX:
        for i in range(3):
            while i:
                if i > 1:
                    break
                i -= 1
    return _MX


class _C:
    X = 2

    def get(self):
        return self.X


if MOD_CONST:
    _R = [_f() for _ in range(1)]
else:
    _R = None
MOD_AFTER = _OD
del _os
assert MOD_CONST == 1
__all__ = ['MOD_CONST', 'MOD_SECOND']
'''

PROBES['m02_top_ifmain.py'] = '''\
"""m02: top-level if-main with deep body."""
import sys


def _run(n):
    total = 0
    for i in range(n):
        try:
            if i % 2:
                total += i
            else:
                total -= i
        finally:
            total = total
    return total


def _main(argv):
    with (open(argv[0]) if argv else sys.stdin) as fh:
        data = fh
    return data if data else None


if __name__ == '__main__':
    if len(sys.argv) > 1:
        for k in range(3):
            while k:
                try:
                    _run(k)
                except ValueError:
                    break
                finally:
                    k -= 1
    else:
        _main([])
'''

PROBES['m03_module_ifchain.py'] = '''\
"""m03: module-level if/elif/else chain with deep arms."""
X = 3
if X == 1:
    A = 1
elif X == 2:
    A = 2
    for i in range(2):
        if i:
            while X:
                try:
                    X -= 1
                    break
                finally:
                    X = X
        else:
            A = i
elif X == 3:
    A = 3
    with _CM() as B:
        if B:
            for k in range(1):
                A += k
else:
    A = 4
    while X:
        if X:
            X -= 1
        else:
            break
'''

PROBES['m04_module_try.py'] = '''\
"""m04: module-level try hosts with deep nesting."""
import json

try:
    CFG = json
except ImportError:
    CFG = None
else:
    HOOK = CFG
finally:
    TAG = 't'

try:
    try:
        for i in range(2):
            with (CFG if 0 else json) as j:
                if i:
                    while i:
                        i -= 1
    except ValueError:
        CFG = 1
    finally:
        DONE = 1
except NameError:
    DONE = 2
'''

PROBES['m05_module_match.py'] = '''\
"""m05: module-level match with nested match."""
MODE = {'op': 'run'}
match MODE:
    case {'op': op} if op:
        for k in ('a', 'b'):
            match k:
                case 'a':
                    FIRST = k
                case _:
                    OTHER = k
    case _:
        MODE = None
'''

PROBES['m06_module_loops.py'] = '''\
"""m06: module-level for/while with else clauses and loop control."""
TOTAL = 0
for i in range(5):
    if i == 3:
        continue
    if i == 4:
        break
    TOTAL += i
else:
    TOTAL = -1
i = 0
while i < 3:
    i += 1
    for j in range(i):
        if j:
            continue
        else:
            break
    else:
        TOTAL += j
else:
    TOTAL += 100
'''

PROBES['m07_module_with.py'] = '''\
"""m07: module-level with, multi-context and deep nest."""
with _A() as a, _B() as b:
    PAIR = (a, b)
with _A() as c:
    for i in range(2):
        try:
            if i:
                with _B() as d:
                    DEEP = (c, d, i)
        finally:
            FIN = i
'''

PROBES['m08_module_stmts.py'] = '''\
"""m08: module-level statement mix (AnnAssign/AugAssign/chain/Expr)."""
import os as _os
import sys
from types import ModuleType as _MT

_K: int = 1
_K += 2
_L = _M = [1, 2]
_N = (x * x for x in range(3))
del _L
assert _os and sys
if __name__ == '__main__':
    print('x')
type(_MT)
GLOBAL_DECL = 0
'''

PROBES['m09_module_deep_cross.py'] = '''\
"""m09: module root depth-7 cross (with/try/for/if/while/match)."""
with _A() as a:
    try:
        for i in range(2):
            if i:
                while i:
                    match i:
                        case 1:
                            RES = 'one'
                        case _:
                            RES = 'other'
    finally:
        FIN = 0
'''

PROBES['m10_module_order.py'] = '''\
"""m10: module statement interleaving with defs and classes."""
V1 = 1


class K1:
    A = V1

    def m(self):
        return self.A


def f1():
    for i in range(2):
        if i:
            try:
                while i:
                    i -= 1
            finally:
                pass
    return i


V2 = f1()


class K2:
    B = V2
    if B:
        C = B

    def n(self):
        match (self.C if 0 else 0):
            case 0:
                return 0
            case _:
                return 1


V3 = [K1, K2]
assert V3
'''

PROBES['m11_module_finonly.py'] = '''\
"""m11: module-level try/finally only plus trailing statements."""
try:
    BASE = 1
finally:
    UNIT = 'f'
AFTER = BASE + 1
for i in range(1):
    AFTER += i
'''

PROBES['m12_module_values.py'] = '''\
"""m12: module-level value forms (Table B cross at root)."""
W = 1 if _F else 2
X = (_F and 1) or (_G and 2) or 3
Y = [i for i in range(3) if i if i > 1]
Z = {'k': _V[0] if _V else 0}
P = _A < _B < _C
Q = f'{W!r:>{len(str(1))}}'


def _cb(v=_X if _X else 0):
    return v


import math as _m

S = _m.sqrt(4) if _m else 0
'''

PROBES['nm01_simple_module.py'] = '''\
"""nm01: shallow module negative control."""
A = 1
B = 2
C = A + B


def f():
    return C


class K:
    D = 3


if __name__ == '__main__':
    print(f())
'''

PROBES['nm02_shallow_module_forms.py'] = '''\
"""nm02: each module form at depth 1 (shallow equivalent of m-probes)."""
if 1:
    R1 = 1
for i in range(1):
    R2 = i
while 0:
    R3 = 1
try:
    R4 = 1
except ValueError:
    R4 = 2
finally:
    R5 = 3
with _A() as a:
    R6 = a
match 1:
    case 1:
        R7 = 1
    case _:
        R7 = 2
try:
    R8 = 1
finally:
    R9 = 2
'''

# ---------------------------------------------------------------- Group 2: ClassDef body

PROBES['c01_class_assign.py'] = '''\
"""c01: class-level assignment forms."""
class CAssign:
    A = 1
    B, C = 2, 3
    D = E = {'k': (A, B)}
    F: int = 4
    G = A + B
    H = [x for x in range(A)]
    I = (lambda v: v * B)(2)
    J = f'v={A!r:>4}'
    K = None

    def get(self):
        return (A if A else C, D['k'], H[0], I, J)
'''

PROBES['c02_class_if.py'] = '''\
"""c02: class-level if/else with deep arms."""
PY2 = 0


class CIf:
    if PY2:
        def items(self):
            return []
    else:
        ITEMS = tuple((i, i * i) for i in range(3))

        def items(self):
            for k, v in ITEMS:
                if v:
                    while k:
                        try:
                            k -= 1
                        finally:
                            pass
            return ITEMS
    if PY2:
        LEGACY = True
    else:
        LEGACY = False


class CIfShallow:
    if PY2:
        TAG = 'old'
    else:
        TAG = 'new'

    def tag(self):
        return self.TAG
'''

PROBES['c03_class_for.py'] = '''\
"""c03: class-level for loop."""
class CFor:
    REG = []
    for _n in range(3):
        REG.append(_n)
        if _n:
            while _n:
                _n -= 1
    NAMES = dict((m, len(m)) for m in ('a', 'bb'))

    def total(self):
        t = 0
        for v in self.REG:
            t += v
        return t
'''

PROBES['c04_class_try.py'] = '''\
"""c04: class-level try/except/else/finally and nested try."""
class CTry:
    try:
        VAL = int('3')
    except ValueError:
        VAL = -1
    else:
        EXTRA = VAL + 1
    finally:
        TAG = 'done'

    def show(self):
        return (self.VAL, self.TAG)


class CTryFin:
    try:
        BASE = 10
    finally:
        UNIT = 'fin'

    def base(self):
        return self.BASE


class CTryNest:
    try:
        try:
            DEEP = 1
        except ValueError:
            DEEP = 2
        finally:
            MID = 3
    except NameError:
        DEEP = 4
    else:
        OUT = 5
    finally:
        LEAF = 6
'''

PROBES['c05_class_with.py'] = '''\
"""c05: class-level with."""
class CWith:
    with _CM() as cm:
        HANDLE = cm

    def use(self):
        return self.HANDLE


class CWithDeep:
    with _CM() as a:
        for i in range(2):
            try:
                if i:
                    with _CM() as b:
                        VAL = (a, b, i)
            finally:
                FLAG = i

    def get(self):
        return self.VAL
'''

PROBES['c06_class_match.py'] = '''\
"""c06: class-level match with nested match."""
class CMatch:
    match (1, 2):
        case (a, b):
            PAIR = (a, b)
        case _:
            PAIR = None

    def p(self):
        return self.PAIR


class CMatchDeep:
    match {'k': [1, 2]}:
        case {'k': [x, *rest]} if x:
            for r in rest:
                if r:
                    match r:
                        case int() as n:
                            GOT = n
                        case _:
                            GOT = None
'''

PROBES['c07_between_methods.py'] = '''\
"""c07: statements interleaved between method definitions."""
class CBetween:
    def first(self):
        return 1
    MID = 'between'
    if MID:
        TAG = MID

    def second(self, v):
        return v + 1
    del MID

    def third(self):
        for i in range(2):
            if i:
                while i:
                    try:
                        i -= 1
                    finally:
                        pass
        return i
    assert True
    import json as _json
    _OTHER = _json

    def fourth(self):
        return 4
'''

PROBES['c08_decorators.py'] = '''\
"""c08: class and method decorators with args."""
DEC = lambda *a, **k: (lambda f: f)


@DEC('cls', flag=1)
class CDeco:
    ATTR = 1

    @staticmethod
    @DEC('s')
    def st(v):
        return v

    @classmethod
    def cm(cls):
        return cls.ATTR

    @property
    def p(self):
        return self.ATTR

    @DEC('m', key=[1, {'k': (2, 3)}])
    def m(self):
        return 2
'''

PROBES['c09_class_import_global.py'] = '''\
"""c09: class-level import and method-level global."""
class CImp:
    import os as _os
    from collections import OrderedDict as _OD
    _M = _os.name if _os else ''

    def m(self):
        return self._M


G = 0


class CGlobal:
    def set_g(self, v):
        global G
        G = v
        if v:
            for i in range(v):
                while i:
                    try:
                        G += 1
                        break
                    finally:
                        pass
        return G

    def get_g(self):
        global G
        return G
'''

PROBES['c10_nested_class.py'] = '''\
"""c10: nested classes with body statements at each level."""
class Outer:
    OA = 1

    class Mid:
        MA = 2
        if MA:
            MB = [i for i in range(MA)]

        class Inner:
            IA = 3
            for _q in range(2):
                QL = _q

            def get(self):
                try:
                    if self.IA:
                        for k in range(2):
                            while k:
                                k -= 1
                finally:
                    pass
                return self.IA

        def mid_get(self):
            return self.IA

    def outer_get(self):
        return self.OA
'''

PROBES['c11_class_func_class.py'] = '''\
"""c11: function and class alternation, deep bodies."""
class CHolder:
    def make(self):
        class Local:
            LV = 1

            def get(self):
                if self.LV:
                    for i in range(1):
                        while i:
                            try:
                                pass
                            finally:
                                pass
                return self.LV
        return Local

    def use(self):
        return self.make()


def top_make(x):
    class Top:
        TV = x

        def t(self):
            return self.TV
    return Top


def deep():
    if 1:
        for i in range(1):
            return top_make(i)
'''

PROBES['c12_class_deep_cross.py'] = '''\
"""c12: class body as root for six-host depth cross."""
class CCross:
    if 1:
        for i in range(2):
            try:
                with _CM() as cm:
                    while i:
                        i -= 1
                        break
            except ValueError:
                ERR = i

    def v(self):
        match (self.ERR if 0 else 0):
            case 0:
                return 0
            case _:
                return 1
'''

PROBES['c13_class_misc.py'] = '''\
"""c13: class-level del/assert/raise/pass/Expr statements."""
class CMisc:
    TMP = 1
    del TMP
    KEEP = 2
    assert KEEP

    def boom(self):
        if 0:
            raise ValueError('x')
        for i in range(2):
            if i > 0:
                while True:
                    if i:
                        break
                    else:
                        continue
        pass
        return None
    print = staticmethod(print)
'''

PROBES['c14_class_docstring.py'] = '''\
"""c14: class docstring and non-docstring first statements."""
class CDoc:
    """Class docstring."""
    A = 1

    def m(self):
        """Method docstring."""
        return self.A


class CNoDoc:
    A = 0
    """Not a docstring (constant expr after assign)."""

    def m(self):
        return self.A


class CDocDeep:
    """Doc plus deep body."""
    if 1:
        for i in range(1):
            while i:
                try:
                    i -= 1
                finally:
                    pass
        B = [i]

    def n(self):
        return B
'''

PROBES['c15_class_augassign.py'] = '''\
"""c15: class-level augassign including ternary RHS (B46 cross)."""
class CAug:
    N = 1
    N += 2
    M = 3
    M *= 2 if N else 1
    L = [1]
    L[0] += M

    def r(self):
        return (self.N, self.M, self.L)
'''

PROBES['nc01_plain_class.py'] = '''\
"""nc01: plain class negative control."""
class KPlain:
    def a(self):
        return 1

    def b(self, v):
        if v:
            for i in range(v):
                while i:
                    i -= 1
        return v
'''

PROBES['nc02_simple_class_body.py'] = '''\
"""nc02: simple class-body negative control."""
class KSimple:
    A = 1
    B = A + 1

    def m(self):
        return self.B
'''

# ---------------------------------------------------------------- Group 3: cross hosts

PROBES['x01_if_deep_hosts.py'] = '''\
"""x01: If as innermost leaf, host depth >= 3."""
def if_in_for():
    for i in range(1):
        if i:
            for j in range(1):
                if j:
                    R = j
    return 1


def if_in_while():
    while 1:
        if 1:
            while 1:
                if 1:
                    R = 1
        break
    return 2


def if_in_try():
    try:
        if 1:
            try:
                if 1:
                    R = 1
            finally:
                F = 1
    except ValueError:
        R = 2
    return 3


def if_in_with():
    with _A() as a:
        if a:
            with _A() as b:
                if b:
                    R = 1
    return 4


def if_in_match():
    match (1, 2):
        case (a, b):
            if a:
                match b:
                    case 2:
                        if b:
                            R = b
    return 5


def if_shallow():
    if 1:
        R = 1
    return 0
'''

PROBES['x02_for_deep_hosts.py'] = '''\
"""x02: For as innermost leaf, host depth >= 3."""
def for_in_if():
    if 1:
        for i in range(1):
            if 1:
                for j in range(1):
                    R = j
    return 1


def for_in_while():
    while 1:
        for i in range(1):
            if 1:
                for j in range(1):
                    R = j
        break
    return 2


def for_in_try():
    try:
        for i in range(1):
            try:
                for j in range(1):
                    R = j
            finally:
                F = 1
    except ValueError:
        R = 2
    return 3


def for_in_with():
    with _A() as a:
        for i in range(1):
            with _A() as b:
                for j in range(1):
                    R = (a, b, j)
    return 4


def for_in_match():
    match (1, 2):
        case (a, b):
            for i in range(1):
                match b:
                    case 2:
                        for j in range(1):
                            R = j
    return 5


def for_shallow():
    for i in range(1):
        R = i
    return 0
'''

PROBES['x03_while_deep_hosts.py'] = '''\
"""x03: While as innermost leaf, host depth >= 3."""
def while_in_if():
    if 1:
        while 1:
            if 1:
                while 1:
                    break
                break
        else:
            R = 1
    return 1


def while_in_for():
    for i in range(1):
        while 1:
            if 1:
                while 1:
                    break
            break
    return 2


def while_in_try():
    try:
        while 1:
            try:
                while 1:
                    break
            finally:
                F = 1
            break
    except ValueError:
        R = 2
    return 3


def while_in_with():
    with _A() as a:
        while 1:
            with _A() as b:
                while 1:
                    break
            break
    return 4


def while_in_match():
    match 1:
        case 1:
            while 1:
                match 1:
                    case 1:
                        while 1:
                            break
                break
    return 5


def while_shallow():
    while 0:
        R = 1
    return 0
'''

PROBES['x04_try_deep_hosts.py'] = '''\
"""x04: Try as innermost leaf, host depth >= 3."""
def try_in_if():
    if 1:
        try:
            if 1:
                try:
                    R = 1
                finally:
                    F = 1
        except ValueError:
            R = 2
    return 1


def try_in_for():
    for i in range(1):
        try:
            for j in range(1):
                try:
                    R = j
                except ValueError:
                    R = 0
        finally:
            F = i
    return 2


def try_in_while():
    while 1:
        try:
            while 1:
                try:
                    R = 1
                finally:
                    F = 1
            break
        except ValueError:
            R = 2
    return 3


def try_in_with():
    with _A() as a:
        try:
            with _A() as b:
                try:
                    R = (a, b)
                finally:
                    F = 1
        except ValueError:
            R = 2
    return 4


def try_in_match():
    match 1:
        case 1:
            try:
                match 1:
                    case 1:
                        try:
                            R = 1
                        finally:
                            F = 1
            except ValueError:
                R = 2
    return 5


def try_shallow():
    try:
        R = 1
    except ValueError:
        R = 2
    finally:
        F = 3
    return 0
'''

PROBES['x05_with_deep_hosts.py'] = '''\
"""x05: With as innermost leaf, host depth >= 3."""
def with_in_if():
    if 1:
        with _A() as a:
            if 1:
                with _A() as b:
                    R = (a, b)
    return 1


def with_in_for():
    for i in range(1):
        with _A() as a:
            if 1:
                with _A() as b:
                    R = (i, a, b)
    return 2


def with_in_try():
    try:
        with _A() as a:
            try:
                with _A() as b:
                    R = (a, b)
            finally:
                F = 1
    except ValueError:
        R = 2
    return 3


def with_in_while():
    while 1:
        with _A() as a:
            with _A() as b:
                R = (a, b)
        break
    return 4


def with_in_match():
    match 1:
        case 1:
            with _A() as a:
                match 1:
                    case 1:
                        with _A() as b:
                            R = (a, b)
    return 5


def with_shallow():
    with _A() as a:
        R = a
    return 0
'''

PROBES['x06_match_deep_hosts.py'] = '''\
"""x06: Match as innermost leaf, host depth >= 3."""
def match_in_if():
    if 1:
        match 1:
            case 1:
                if 1:
                    match 2:
                        case 2:
                            R = 2
    return 1


def match_in_for():
    for i in range(1):
        match i:
            case 0:
                for j in range(1):
                    match j:
                        case 0:
                            R = j
    return 2


def match_in_try():
    try:
        match 1:
            case 1:
                try:
                    match 2:
                        case 2:
                            R = 2
                finally:
                    F = 1
    except ValueError:
        R = 0
    return 3


def match_in_with():
    with _A() as a:
        match 1:
            case 1:
                with _A() as b:
                    match 2:
                        case 2:
                            R = (a, b)
    return 4


def match_in_while():
    while 1:
        match 1:
            case 1:
                while 1:
                    match 2:
                        case 2:
                            R = 2
                    break
        break
    return 5


def match_shallow():
    match 1:
        case 1:
            R = 1
        case _:
            R = 2
    return 0
'''

PROBES['x07_trystar_deep.py'] = '''\
"""x07: except* at depth >= 3 (A7/C3 depth extrapolation)."""
def ts_shallow():
    try:
        raise ExceptionGroup('g', [ValueError('x')])
    except* ValueError as eg:
        R = eg
    return 1


def ts_in_for():
    for i in range(1):
        try:
            if i:
                try:
                    raise ExceptionGroup('g', [TypeError('t')])
                except* TypeError as eg:
                    R = eg
        finally:
            F = i
    return 2


def ts_with_fin():
    try:
        with _A():
            try:
                raise ExceptionGroup('g', [ValueError('v')])
            except* ValueError as eg:
                R = 1
    finally:
        F = 2
    return 3
'''

PROBES['x08_stmt_leaves.py'] = '''\
"""x08: statement-form leaves in deep hosts."""
def assert_leaf():
    for i in range(1):
        if i:
            while i:
                assert i or 1
    return 1


def raise_leaf():
    try:
        for i in range(1):
            if i:
                try:
                    raise ValueError(i)
                finally:
                    F = i
    except ValueError:
        R = 1
    return 2


def return_leaf():
    for i in range(1):
        if i:
            while i:
                if i:
                    return i
    return None


def delete_leaf():
    obj = [1, 2, 3]
    for i in range(1):
        if i:
            try:
                del obj[0]
            finally:
                pass
    return obj


def assign_leaves():
    out = []
    for i in range(1):
        if i:
            out += [x for x in range(2)]
            aug = 0
            aug += i
            ann: int = i
            ann += aug
            out.append((aug, ann))
    return out


def import_leaf():
    for i in range(1):
        if i:
            with _A():
                import json as _j
                global IMPORT_G
                IMPORT_G = _j
    return 3
'''

PROBES['x09_funcdef_hosts.py'] = '''\
"""x09: FunctionDef/AsyncFunctionDef as statements in deep hosts."""
def def_in_if():
    if 1:
        for i in range(1):
            def inner(v):
                return v + i
            r = inner(1)
    return r


def def_in_try():
    try:
        with _A():
            def inner2(v):
                if v:
                    for k in range(v):
                        while k:
                            k -= 1
                return k
    finally:
        F = 1
    return inner2(2)


class AHost:
    async def a1(self):
        async with _A() as a:
            if a:
                for i in range(2):
                    await self.a2(i)

    async def a2(self, v):
        async for i in _AIT():
            if i:
                acc = [x async for x in _AIT()]
                return i

    def sync_use(self):
        return (self.a1, self.a2)
'''

PROBES['x10_handler_hosts.py'] = '''\
"""x10: ExceptHandler bodies as deep hosts."""
def h_basic():
    try:
        X = 1
    except ValueError as e:
        for i in range(2):
            if i:
                while i:
                    try:
                        i -= 1
                    except ValueError:
                        break
    except (TypeError, KeyError) as e2:
        with _A():
            match e2:
                case TypeError():
                    R = 't'
                case _:
                    R = 'o'
    else:
        E = 0
    finally:
        F = 9
    return X


def h_shallow():
    try:
        X = 1
    except ValueError:
        R = 2
    return X
'''

PROBES['nx01_shallow_hosts.py'] = '''\
"""nx01: six hosts at depth 1, shallow equivalent negative control."""
def s_if():
    if 1:
        R = 1
    return 1


def s_for():
    for i in range(1):
        R = i
    return 2


def s_while():
    while 0:
        R = 1
    return 3


def s_try():
    try:
        R = 1
    except ValueError:
        R = 2
    finally:
        F = 3
    return 4


def s_with():
    with _A() as a:
        R = a
    return 5


def s_match():
    match 1:
        case 1:
            R = 1
        case _:
            R = 2
    return 6
'''


def main():
    written = 0
    for name, src in sorted(PROBES.items()):
        path = os.path.join(HERE, name)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(src)
        written += 1
    print('wrote %d probe files to %s' % (written, HERE))


if __name__ == '__main__':
    main()
