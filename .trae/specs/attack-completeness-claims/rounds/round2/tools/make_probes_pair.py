#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 探针第五批：同文件内的**最小对**（唯一差异 = try 体末尾一条语句）。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROBES = os.path.abspath(os.path.join(HERE, '..', 'probes'))

P = {}

P['l0_f1_minpair_same_file.py'] = '''"""AT-02/AT-04 同文件最小对：m1 与 m2 唯一差异 = try 体末尾多一条 g(x)"""


def m1(items, g):
    for x in items:
        try:
            if x:
                continue
        finally:
            g(0)


def m2(items, g):
    for x in items:
        try:
            if x:
                continue
            g(x)
        finally:
            g(0)
'''

P['l0_f2_minpair_for_else_same_file.py'] = '''"""AT-04 同文件最小对：n1（for-else 被塌陷）与 n2（无 else）对照"""


def n1(items, g):
    for x in items:
        try:
            if x:
                break
            g(x)
        finally:
            g(0)


def n2(items, g):
    for x in items:
        try:
            if x:
                break
            g(x)
        finally:
            g(0)
        g(1)
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
