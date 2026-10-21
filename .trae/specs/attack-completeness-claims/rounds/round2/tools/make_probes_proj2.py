#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 探针第四批：修正 e4 语法 + for x match 的变量分离（continue / with / 无）。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROBES = os.path.abspath(os.path.join(HERE, '..', 'probes'))

P = {}

P['l0_e4_proj_try_for.py'] = '''"""AT-02 二元投影 4/5（修正）: try x for（a4 的 try+for 子投影）"""


def e4(xs):
    try:
        for x in xs:
            print(x)
    except Exception:
        pass
'''

P['l0_e11_proj_for_match_plain.py'] = '''"""AT-02 for x match 变量分离 1/3: case 体无 continue"""


def e11(v):
    for x in v:
        match x:
            case 0:
                print('zero')
            case _:
                print('other')
'''

P['l0_e12_proj_for_match_continue.py'] = '''"""AT-02 for x match 变量分离 2/3: case 体含 continue"""


def e12(v):
    for x in v:
        match x:
            case 0:
                continue
            case _:
                continue
'''

P['l0_e13_proj_for_match_with.py'] = '''"""AT-02 for x match 变量分离 3/3: case 体含 with（a2 的 with 子投影在 match 内）"""


def e13(v):
    for x in v:
        match x:
            case 0:
                with open('f') as fh:
                    print(fh)
            case _:
                print('other')
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
