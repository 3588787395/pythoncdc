#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2 微 VM：按 dis 指令精确走控制流，打印关键 offset 的栈。"""
import dis
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = open(sys.argv[1], encoding='utf-8').read()
ns = {}
exec(compile(SRC, 't', 'exec'), ns)
FNAME = sys.argv[2]
FUNC = ns[FNAME]
ARGS = eval(sys.argv[3])
WATCH = set(int(x, 0) for x in sys.argv[4:])

code = FUNC.__code__
ins = {}
for it in dis.get_instructions(code):
    ins[it.offset] = it
order = sorted(ins)


def nextoff(off):
    for k in order:
        if k > off:
            return k
    return None


def run(args):
    st = []
    off = 0
    loc = dict(zip(code.co_varnames, args))
    for _ in range(1000):
        if off in WATCH:
            print('  @%d %-30s stack=%r' % (off, ins[off].opname, st))
        i = ins[off]
        op = i.opname
        if op in ('RESUME', 'CACHE', 'NOP', 'PRECALL', 'COPY_FREE_VARS',
                  'MAKE_CELL', 'PUSH_NULL'):
            off = nextoff(off)
            continue
        if op == 'LOAD_GLOBAL':
            import builtins
            nm = i.argval
            if nm is None:
                st.append(None)
            elif nm in ns:
                st.append(ns[nm])
            else:
                st.append(getattr(builtins, nm, nm))
            off = nextoff(off)
            continue
        if op == 'LOAD_CONST':
            st.append(i.argval)
            off = nextoff(off)
            continue
        if op == 'LOAD_FAST':
            st.append(loc[i.argval])
            off = nextoff(off)
            continue
        if op == 'CALL':
            n = i.arg
            a = [st.pop() for _ in range(n)]
            fn = st.pop()
            st.append(fn(*a))
            off = nextoff(off)
            continue
        if op == 'GET_ITER':
            st.append(iter(st.pop()))
            off = nextoff(off)
            continue
        if op == 'FOR_ITER':
            try:
                st.append(next(st[-1]))
                off = nextoff(off)
            except StopIteration:
                st.pop()
                off = i.argval
            continue
        if op == 'STORE_FAST':
            loc[i.argval] = st.pop()
            off = nextoff(off)
            continue
        if op == 'POP_JUMP_FORWARD_IF_FALSE':
            v = st.pop()
            off = i.argval if not v else nextoff(off)
            continue
        if op == 'POP_JUMP_FORWARD_IF_TRUE':
            v = st.pop()
            off = i.argval if v else nextoff(off)
            continue
        if op == 'JUMP_IF_FALSE_OR_POP':
            if not st[-1]:
                off = i.argval
            else:
                st.pop()
                off = nextoff(off)
            continue
        if op in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
            off = i.argval
            continue
        if op == 'COMPARE_OP':
            r = st.pop()
            l = st.pop()
            st.append(eval('%r %s %r' % (l, i.argval, r)))
            off = nextoff(off)
            continue
        if op == 'SWAP':
            n = i.arg
            st[-1], st[-n] = st[-n], st[-1]
            off = nextoff(off)
            continue
        if op == 'POP_TOP':
            st.pop()
            off = nextoff(off)
            continue
        if op == 'RETURN_VALUE':
            return st.pop()
        if op == 'RETURN_CONST':
            return i.argval
        print('  UNHANDLED', op)
        return None
    return 'LOOP?'


print('result:', run(ARGS))
