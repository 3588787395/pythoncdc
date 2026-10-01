#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r3 首分歧定位器：orig pyc vs OK.py 重编译 pyc 的逐 code object 指令对照。

用法：python _r3_firstdiff.py <x.pyc> <xOK.py> [qualname前缀]
输出每个 code object 的首条分歧（offset/opname/argval 三元对照）。
只读判据配套，不修改 core/ 与 scripts/。
"""
import sys
import os
import marshal
import importlib.util
import dis
import tempfile

NOISE = {'RESUME', 'CACHE', 'EXTENDED_ARG', 'PRECALL'}


def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def walk(code, prefix=''):
    yield prefix or '<module>', code
    for c in code.co_consts:
        if hasattr(c, 'co_code'):
            yield from walk(c, (prefix + '.' if prefix else '') + c.co_name)


def instrs(code):
    out = []
    for i in dis.get_instructions(code):
        if i.opname in NOISE:
            continue
        out.append((i.offset, i.opname, i.argval))
    return out


def first_diff(name, ci, cj):
    a, b = instrs(ci), instrs(cj)
    n = max(len(a), len(b))
    for idx in range(n):
        ea = a[idx] if idx < len(a) else None
        eb = b[idx] if idx < len(b) else None
        if ea != eb:
            return idx, a, b, ea, eb
    return None, a, b, None, None


def main():
    pyc, src = sys.argv[1], sys.argv[2]
    prefix_filter = sys.argv[3] if len(sys.argv) > 3 else ''
    co = load_pyc(pyc)
    tmp = tempfile.mktemp(suffix='.py')
    with open(src, encoding='utf-8-sig') as f:
        text = f.read()
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(text)
    try:
        cj = compile(text, os.path.basename(pyc), 'exec', dont_inherit=True)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    for name, ci in walk(co):
        if prefix_filter and prefix_filter not in name:
            continue
        try:
            cj2 = dict((n2, c2) for n2, c2 in walk(cj)).get(name)
        except Exception:
            cj2 = None
        if cj2 is None:
            print(f'[{name}] MISSING in decompiled tree')
            continue
        idx, a, b, ea, eb = first_diff(name, ci, cj2)
        la, lb = len(a), len(b)
        if idx is None:
            continue
        print(f'[{name}] first_diff @{idx} (orig {la} instrs / decomp {lb})')
        ctx0 = max(0, idx - 3)
        for k in range(ctx0, min(idx + 3, max(la, lb))):
            sa = a[k] if k < la else '-'
            sb = b[k] if k < lb else '-'
            mark = '>>' if k == idx else '  '
            print(f'  {mark} o{k}: {sa}   d{k}: {sb}')


if __name__ == '__main__':
    main()
