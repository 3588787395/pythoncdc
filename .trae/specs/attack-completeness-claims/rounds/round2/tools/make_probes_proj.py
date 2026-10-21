#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 探针第三批：三元构造的**二元投影**（binary-closure 前提的对照）+ 语义强化最小对。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROBES = os.path.abspath(os.path.join(HERE, '..', 'probes'))

P = {}

# ── AT-02 二元投影（对照三元失败构造） ──────────────────────────────────
P['l0_e1_proj_for_match.py'] = '''"""AT-02 二元投影 1/5: for x match（a2 的 match 子投影）"""


def e1(v):
    for x in v:
        match x:
            case 0:
                continue
            case _:
                continue
'''

P['l0_e2_proj_for_with.py'] = '''"""AT-02 二元投影 2/5: for x with（a2 的 with 子投影）"""


def e2(v):
    for x in v:
        with open('f') as fh:
            print(fh)
'''

P['l0_e3_proj_while_try.py'] = '''"""AT-02 二元投影 3/5: while x try（a4 的 while+try 子投影）"""


def e3(xs):
    while True:
        try:
            print(1)
        except Exception:
            break
'''

P['l0_e4_proj_try_for.py'] = '''"""AT-02 二元投影 4/5: try x for（a4 的 try+for 子投影）"""


def e4(xs):
    try:
        for x in xs:
            print(x)
    except Exception:
        break
'''

P['l0_e5_proj_while_for.py'] = '''"""AT-02 二元投影 5/5: while x for（a4 的 while+for 子投影）"""


def e5(xs):
    while True:
        for x in xs:
            print(x)
'''

P['l0_e6_proj_if_for_else.py'] = '''"""AT-04 二元投影: if x for-else（b5 的 if+for-else 子投影）"""


def e6(xs):
    if xs:
        for x in xs:
            print(x)
        else:
            print('else')
'''

P['l0_e7_proj_try_for_else.py'] = '''"""AT-04 二元投影: try x for-else（b5 的 try+for-else 子投影）"""


def e7(xs):
    try:
        for x in xs:
            print(x)
        else:
            print('else')
    except Exception:
        pass
'''

# ── 语义强化最小对（把「形状差异」升级为「语义差异」） ────────────────────
P['l0_e8_for_else_break_in_if_in_try.py'] = '''"""AT-04 语义强化: for-else 体含 break 时，else 归属错误即产生**可观测语义差**"""


def e8(xs):
    try:
        if xs:
            for x in xs:
                if x:
                    break
                print(x)
            else:
                print('else')
    except Exception:
        pass
'''

P['l0_e9_minpair_try_only_if_continue.py'] = '''"""AT-02/AT-04 最小对 A: try 体只有 if+continue（无后续语句）"""


def e9(items, g):
    for x in items:
        try:
            if x:
                continue
        finally:
            g(0)
'''

P['l0_e10_minpair_try_only_continue.py'] = '''"""AT-02/AT-04 最小对 B: try 体只有 continue（无 if）"""


def e10(xs):
    for a in xs:
        try:
            continue
        finally:
            print('fin')
'''


def main():
    os.makedirs(PROBES, exist_ok=True)
    for name, src in sorted(P.items()):
        with open(os.path.join(PROBES, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write(src)
        print('wrote %s' % name)
    return 0


if __name__ == '__main__':
    sys.exit(main())
