#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round5 只读首分歧对照器（code object 归一化逐指令 diff）。不改 core/、不改 scripts/。

用法：python _r5v5_firstdiff.py <stem>    # stem 例：r5v5_01_module_root
比对：原 pyc（marshal 载入）vs 现磁盘 <stem>OK.py 重编译，逐 code object 取首条 (opname,argval)
差异指令。仅用于定位机制，不做判定（判定唯一 = scripts/pyc_verify.py）。
"""
import dis
import marshal
import os
import py_compile
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))


def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def norm_arg(arg):
    if isinstance(arg, types.CodeType):
        return '<code:%s>' % arg.co_name
    if isinstance(arg, frozenset):
        return 'frozenset(%s)' % sorted(repr(x) for x in arg)
    return repr(arg)


def instrs(code):
    seq = []
    for ins in dis.get_instructions(code):
        if ins.opname == 'CACHE':
            continue
        seq.append((ins.opname, norm_arg(ins.argval)))
    return seq


def collect(code, prefix, out):
    out[prefix] = code
    for con in code.co_consts:
        if isinstance(con, types.CodeType):
            collect(con, prefix + '.' + con.co_name, out)
    return out


def main():
    stem = sys.argv[1]
    pyc = os.path.join(HERE, stem + '.pyc')
    ok = os.path.join(HERE, stem + 'OK.py')
    tmp = os.path.join(tempfile.gettempdir(), stem + '_recomp.pyc')
    py_compile.compile(ok, cfile=tmp, doraise=True, optimize=0)

    a = collect(load_pyc(pyc), '<module>', {})
    b = collect(load_pyc(tmp), '<module>', {})
    for name in sorted(set(a) | set(b)):
        if name not in a:
            print('ONLY_IN_OK', name)
            continue
        if name not in b:
            print('ONLY_IN_ORIG', name)
            continue
        ia, ib = instrs(a[name]), instrs(b[name])
        if ia == ib:
            continue
        print('=== %s  orig=%d ok=%d' % (name, len(ia), len(ib)))
        n = max(len(ia), len(ib))
        shown = 0
        for i in range(n):
            x = ia[i] if i < len(ia) else None
            y = ib[i] if i < len(ib) else None
            if x != y:
                print('  @%d orig=%s  ok=%s' % (i, x, y))
                shown += 1
                if shown >= 6:
                    break
    try:
        os.remove(tmp)
    except OSError:
        pass


if __name__ == '__main__':
    main()