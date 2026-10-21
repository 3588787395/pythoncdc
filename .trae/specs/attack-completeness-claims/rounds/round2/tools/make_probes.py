#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 理论层攻击探针生成器（写 .py 源；.pyc 由 l0_probe_driver.py 编译）。

纪律：只写 rounds/round2/probes/ 目录；不触碰 core/**、tests/**、wiki/**。
每条探针对应 ATTACK_L0_THEORY.md 中一个攻击项的最小构造。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROBES = os.path.abspath(os.path.join(HERE, '..', 'probes'))

PROBE_SOURCES = {}

# ── AT-02 归纳步：二元组合封闭是否蕴含三元组合 ────────────────────────────
PROBE_SOURCES['l0_a1_triple_if_for_try.py'] = '''"""AT-02: if x for x try —— 三元嵌套，try 体含 continue/break"""


def a1(xs):
    if xs:
        for x in xs:
            try:
                if x:
                    continue
                else:
                    break
            except ValueError:
                pass
        else:
            print('for-else')
    return 0
'''

PROBE_SOURCES['l0_a2_triple_for_match_with.py'] = '''"""AT-02: for x match x with —— 三元嵌套，case 体含 with + continue"""


def a2(v):
    for x in v:
        match x:
            case 0:
                with open('f') as fh:
                    print(fh)
            case _:
                continue
    else:
        print('else')
'''

PROBE_SOURCES['l0_a3_triple_nested_finally_continue.py'] = '''"""AT-02/B142: for x try/finally x try/finally —— 两级 finally 副本 + continue"""


def a3(xs):
    for x in xs:
        try:
            try:
                if x:
                    continue
                else:
                    break
            finally:
                print('inner-fin')
        finally:
            print('outer-fin')
'''

PROBE_SOURCES['l0_a4_triple_while_try_for.py'] = '''"""AT-02: while x try x for —— 三元嵌套，for-else + try-else 混合"""


def a4(xs):
    while True:
        try:
            for x in xs:
                if x:
                    break
                else:
                    continue
        except Exception:
            break
        else:
            continue
'''

# ── AT-04/AT-05 「必须知道外层」类判据：loop_else 归属守卫覆盖面 ──────────
PROBE_SOURCES['l0_b1_for_else_in_with.py'] = '''"""AT-04: for-else 位于 with 体内（守卫只列 TryExceptRegion 的子集检验）"""


def b1(xs):
    with open('f') as fh:
        for x in xs:
            print(x)
        else:
            print('for-else')
    return fh
'''

PROBE_SOURCES['l0_b2_for_else_in_match.py'] = '''"""AT-04: for-else 位于 match case 体内"""


def b2(v):
    match v:
        case [x]:
            for i in range(x):
                print(i)
            else:
                print('else')
        case _:
            pass
'''

PROBE_SOURCES['l0_b3_for_else_in_try_except.py'] = '''"""AT-04: for-else 位于 try/except 体内（无 finally）"""


def b3(xs):
    try:
        for x in xs:
            print(x)
        else:
            print('else')
    except Exception:
        pass
'''

PROBE_SOURCES['l0_b4_nested_for_else.py'] = '''"""AT-04: 内外双层 for-else（B109 nested_loop_else 形态）"""


def b4(xs):
    for a in xs:
        for b in xs:
            print(a, b)
        else:
            print('inner-else')
    else:
        print('outer-else')
'''

PROBE_SOURCES['l0_b5_for_else_in_if_in_try.py'] = '''"""AT-04: for-else 位于 try 体内的 if 分支中"""


def b5(xs):
    try:
        if xs:
            for x in xs:
                print(x)
            else:
                print('else')
    except Exception:
        pass
'''

# ── AT-01 非局部信息通道：continue 目标 / 外层循环回边 / handler break ────
PROBE_SOURCES['l0_c1_outer_continue_inner_loop.py'] = '''"""AT-01: 内外双循环各自 continue —— 全局 CONTINUE 角色表的「哪一层循环」限定丢失"""


def c1(xs):
    for a in xs:
        for b in xs:
            if b:
                continue
        if a:
            continue
'''

PROBE_SOURCES['l0_c2_inner_exit_to_outer_backedge.py'] = '''"""AT-01: 内层循环自然出口落到外层循环回边块（全局角色 CONTINUE 命中外层）"""


def c2(xs):
    for a in xs:
        for b in xs:
            print(b)
'''

PROBE_SOURCES['l0_c3_break_in_handler.py'] = '''"""AT-04: handler 体内 break（B140 形态），break 落点在循环之外"""


def c3(xs):
    for a in xs:
        try:
            print(a)
        except Exception:
            break
    return 0
'''

PROBE_SOURCES['l0_c4_finally_copy_continue.py'] = '''"""AT-01/AT-04: finally 副本 + continue —— 副本归属与 continue 目标同时命中"""


def c4(xs):
    for a in xs:
        try:
            continue
        finally:
            print('fin')
'''

PROBE_SOURCES['l0_c5_continue_in_nested_try_finally.py'] = '''"""AT-01/AT-04: try/finally 内 continue，finally 副本与 continue 目标双重归属"""


def c5(xs):
    for a in xs:
        try:
            if a:
                continue
        finally:
            print('fin')
'''


def main():
    os.makedirs(PROBES, exist_ok=True)
    for name, src in sorted(PROBE_SOURCES.items()):
        path = os.path.join(PROBES, name)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(src)
        print('wrote %s (%d bytes)' % (name, len(src.encode('utf-8'))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
