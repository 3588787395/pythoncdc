import dis
import sys

CASES = {}

CASES['A_continue_in_try_far'] = """
def f(syms, lg):
    out = {}
    for s in syms:
        try:
            if lg.flag(s) == 0:
                if lg.k(s):
                    out[s] = 1
                else:
                    out[s] = 2
                continue
            if lg.k2(s):
                out[s] = 3
            else:
                out[s] = 4
        except BaseException:
            lg.err(s)
    return out
"""

CASES['B_nested_if_try'] = """
def f(syms, lg):
    out = {}
    for s in syms:
        try:
            if lg.flag(s) == 0:
                if len(s) == 0:
                    out[s] = 1
                    continue
                out[s] = 2
                if out:
                    out[s] = 3
                else:
                    out[s] = 4
            elif len(s):
                out[s] = 5
            else:
                out[s] = 6
        except BaseException:
            lg.err(s)
    return out
"""

CASES['C_deep_before_far'] = """
def f(syms, lg):
    out = {}
    for s in syms:
        try:
            lg.a(s)
            lg.b(s)
            lg.c(s)
            lg.d(s)
            lg.e(s)
            lg.f(s)
            lg.g(s)
            lg.h(s)
            lg.i(s)
            lg.j(s)
            lg.k(s)
            lg.l(s)
            lg.m(s)
            lg.n(s)
            lg.o(s)
            lg.p(s)
            lg.q(s)
            lg.r(s)
            lg.s2(s)
            lg.t(s)
            lg.u(s)
            lg.v(s)
            lg.w(s)
            lg.x(s)
            lg.y(s)
            lg.z(s)
            if len(s) == 0:
                out[s] = 1
            else:
                out[s] = 2
            continue
        except BaseException:
            lg.err(s)
    return out
"""


def dup_bwd(code):
    ins = [i for i in dis.get_instructions(code) if i.opname != 'CACHE']
    hits = []
    for a, b in zip(ins, ins[1:]):
        if a.opname.startswith('JUMP_BACKWARD') and b.opname == a.opname and a.argval == b.argval:
            hits.append((a.offset, b.offset, a.argval))
    return hits


for k, src in CASES.items():
    mod = compile(src, '<synth>', 'exec')
    f = [c for c in mod.co_consts if hasattr(c, 'co_name') and c.co_name == 'f'][0]
    print('%-22s dup_backward=%s' % (k, dup_bwd(f)))
