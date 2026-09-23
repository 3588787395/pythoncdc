# -*- coding: utf-8 -*-
"""Instruction-sequence diff between a real .pyc and a freshly produced .py.

usage: python -X utf8 diff52.py <pyc-rel-under-site-packages> <prod-py> <fn-or-substr>
"""
import dis
import importlib.util
import marshal
import os
import py_compile
import sys
import difflib

REPO = r'F:\Downloads\pythoncdc-main'
NOISE = {'NOP', 'CACHE', 'PRECALL', 'EXTENDED_ARG'}
sys.stdout.reconfigure(encoding='utf-8')


def load_map(p):
    with open(p, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    out = {}

    def w(c, pfx=''):
        out.setdefault(pfx + c.co_name, c)
        for k in c.co_consts:
            if hasattr(k, 'co_name'):
                w(k, pfx + c.co_name + '.')
    w(code)
    return out


pyc = os.path.join(REPO, 'site-packages', sys.argv[1].replace('/', os.sep))
prod = sys.argv[2]
want = sys.argv[3]
o = load_map(pyc)
cf = py_compile.compile(prod, doraise=True, quiet=2)
d = load_map(cf)


def filt(c):
    return [i for i in dis.get_instructions(c) if i.opname not in NOISE]


JUMPS = {'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD_NO_INTERRUPT',
         'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_NONE',
         'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
         'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
         'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_NONE', 'POP_JUMP_IF_NOT_NONE',
         'FOR_ITER', 'SEND'}


def sfx(i):
    return '%s %s' % (i.opname, '<T>' if i.opname in JUMPS else i.argrepr)


def seq(cc):
    return [sfx(i) for i in filt(cc)]


for name in sorted(o):
    if want not in name:
        continue
    if d.get(name) is None:
        print('%s MISSING in product' % name)
        continue
    fo, fd = filt(o[name]), filt(d[name])
    print('==== %s orig=%d decomp=%d delta=%d' % (name, len(fo), len(fd), len(fd) - len(fo)))
    so = seq(o[name])
    sd = seq(d[name])
    sm = difflib.SequenceMatcher(None, so, sd, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        print('  --- %s orig[%d:%d] decomp[%d:%d]' % (tag, i1, i2, j1, j2))
        for k in range(max(0, i1 - 6), min(len(so), i2 + 6)):
            print('     O%4d %s%s' % (k, '*' if i1 <= k < i2 else ' ', so[k][:78]))
        for k in range(max(0, j1 - 6), min(len(sd), j2 + 6)):
            print('     %sD%4d %s' % ('>>' if j1 <= k < j2 else '  ', k, sd[k][:78]))
        print()
