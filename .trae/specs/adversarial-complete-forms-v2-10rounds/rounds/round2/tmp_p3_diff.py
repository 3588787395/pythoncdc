#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时诊断：编译 OK.py 并逐单元比对字节码，输出差异指令流。
用法：python tmp_p3_diff.py <pyc> [单元名过滤]
"""
import io
import dis
import sys
import os
import py_compile
import contextlib
import marshal
import importlib.util

ROOT = r"F:\Downloads\pythoncdc-main"


def load_pyc_code(pyc):
    with open(pyc, 'rb') as f:
        data = f.read()
    return marshal.loads(data[16:])


def code_infos(code, prefix=''):
    infos = {}
    name = prefix + code.co_name
    infos[name] = code
    for c in code.co_consts:
        if hasattr(c, 'co_code'):
            infos.update(code_infos(c, name + '.'))
    return infos


def render(code):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        dis.dis(code, depth=0)
    return out.getvalue()


def main():
    pyc = sys.argv[1]
    filt = sys.argv[2] if len(sys.argv) > 2 else None
    okpy = pyc[:-4] + 'OK.py'
    cfile = okpy + 'c'
    py_compile.compile(okpy, cfile=cfile, doraise=True, optimize=0)
    new_root = load_pyc_code(cfile)
    old_root = load_pyc_code(pyc)
    old = code_infos(old_root)
    new = code_infos(new_root)
    status = 0
    for name in sorted(set(old) | set(new)):
        if filt and filt not in name:
            continue
        if name not in old:
            print('EXTRA:', name); status = 1; continue
        if name not in new:
            print('MISSING:', name); status = 1; continue
        o, n = old[name], new[name]
        if o.co_code == n.co_code and o.co_consts == n.co_consts:
            print('MATCH :', name)
        else:
            print('DIFF  :', name)
            ol = render(o).splitlines()
            nl = render(n).splitlines()
            import difflib
            for line in difflib.unified_diff(ol, nl, 'orig', 'recomp', lineterm='', n=2):
                print('   ', line)
            if o.co_consts != n.co_consts:
                print('    consts orig:', o.co_consts)
                print('    consts recomp:', n.co_consts)
            status = 1
    sys.exit(status)


if __name__ == '__main__':
    main()
