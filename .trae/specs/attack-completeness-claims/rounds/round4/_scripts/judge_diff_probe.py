#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：对单个 (pyc, 产物) 对做「产物 vs 变异产物」的字节码级 diff，
解释判据为何抓到 / 未抓到某族变异。

用法： python -X utf8 judge_diff_probe.py <pyc> <family>
"""
from __future__ import annotations

import dis
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mutation_lib  # noqa: E402


def disasm(path):
    out = []
    src = open(path, 'rb').read()
    code = compile(src, os.path.basename(path), 'exec')
    def walk(c, prefix=''):
        for ins in dis.get_instructions(c):
            out.append('%s%-22s arg=%-4s argval=%r' % (prefix, ins.opname, ins.arg, ins.argval))
        for k in c.co_consts:
            if hasattr(k, 'co_code'):
                walk(k, prefix + k.co_name + '.')
    walk(code)
    return out


def main():
    pyc = os.path.abspath(sys.argv[1])
    fam = sys.argv[2]
    prod = pyc[:-4] + 'OK.py'
    raw = open(prod, 'rb').read()
    mut, site = mutation_lib.apply_mutation(fam, raw)
    if mut is None:
        print('NOT APPLICABLE:', site)
        return
    out = os.path.join(HERE, '_diffprobe_%s.py' % fam)
    open(out, 'wb').write(mut)
    print('pyc     :', pyc)
    print('product :', prod)
    print('mutation:', site)
    print('mutated file written to', out)
    a = disasm(prod)
    b = disasm(out)
    import difflib
    diff = list(difflib.unified_diff(a, b, 'product', 'mutated', lineterm='', n=1))
    print('\n'.join(diff[:60]) if diff else '(no disassembly difference)')


if __name__ == '__main__':
    main()
