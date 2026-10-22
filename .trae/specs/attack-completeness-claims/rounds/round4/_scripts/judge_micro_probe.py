#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：判据本体的**常量/标识符比较语义**微观探针。

问题：
  1) 判据 compare_instruction 比较 `argval`（Python 对象 `==`）。那么
     int 1 / float 1.0 / bool True 之间的可分辨性如何？
  2) LOAD_FAST 的 argval 是**名字**还是**下标**？改名是否可见？
  3) co_consts 的索引是否随常量替换而移动（索引漂移是否被看见）？
  4) docstring / 注解 是否进入 co_consts 且是否被引用？

用法： python -X utf8 judge_micro_probe.py
"""
from __future__ import annotations

import dis
import io


def dump(code, label):
    print('--- %s ---' % label)
    for ins in dis.get_instructions(code):
        print('  %-22s arg=%-3s argval=%r' % (ins.opname, ins.arg, ins.argval))
    print('  co_consts = %r' % (code.co_consts,))
    print('  co_varnames = %r' % (code.co_varnames,))


def main():
    src = (
        'def f(a):\n'
        '    x = 1\n'
        '    y = 1.0\n'
        '    z = True\n'
        '    w = a\n'
        '    return x, y, z, w\n'
    )
    code = compile(src, '<probe>', 'exec')
    dump(code, 'const pool (1 / 1.0 / True)')

    # 常量替换后索引是否移动
    c1 = compile('x = 1\n', '<p>', 'exec')
    c2 = compile('x = True\n', '<p>', 'exec')
    c3 = compile('x = 1.0\n', '<p>', 'exec')
    print('\nconst index of LOAD_CONST: 1->%s  True->%s  1.0->%s'
          % (c1.co_consts.index(1), c2.co_consts.index(True), c3.co_consts.index(1.0)))
    print('equality: 1 == True -> %s ; 1 == 1.0 -> %s ; True == 1.0 -> %s'
          % (1 == True, 1 == 1.0, True == 1.0))

    # docstring / 注解 是否被指令引用
    c4 = compile('def g():\n    """DOC"""\n    v: int = 1\n    return v\n', '<p>', 'exec')
    fn = [k for k in c4.co_consts if hasattr(k, 'co_name') and k.co_name == 'g'][0]
    dump(fn, 'docstring + local annotation')
    print('  docstring referenced by an instruction?',
          any(ins.opname == 'LOAD_CONST' and ins.argval == 'DOC' for ins in dis.get_instructions(fn)))
    print('  annotation in co_consts?', 'int' in fn.co_consts)


if __name__ == '__main__':
    main()
