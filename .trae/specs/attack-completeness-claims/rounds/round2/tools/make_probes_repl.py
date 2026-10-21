#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 探针第二批：既有语料形状的**逐字复刻**（用于区分「新破口」与「已登记残余」）。

纪律：源逐字取自仓库既有探针，只加文件头注释；不修改任何既有文件。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROBES = os.path.abspath(os.path.join(HERE, '..', 'probes'))

REPL = {}

# 逐字复刻 test_repros/round19_cont/r19c_23_neg_continue_in_try_finally.py
REPL['l0_d1_repl_r19c23_continue_in_try_finally.py'] = '''"""逐字复刻 r19c_23_neg_continue_in_try_finally（既有负对照形状）"""


def f(items, g):
    for x in items:
        try:
            if x:
                continue
            g(x)
        finally:
            g(0)
'''

# 逐字复刻 test_repros/round19_cont/r19c_04_anchor_try_finally.py
REPL['l0_d2_repl_r19c04_try_finally.py'] = '''"""逐字复刻 r19c_04_anchor_try_finally（既有锚点形状：if 内含 try/finally）"""


def f(items, g):
    for x in items:
        if x:
            try:
                g(x)
            finally:
                g(0)
'''

# 逐字复刻 test_repros/round10/r10_21_fin_loopctrl.py 的三个函数
REPL['l0_d3_repl_r10_21_fin_loopctrl.py'] = '''"""逐字复刻 r10_21_fin_loopctrl（finally 体含 continue/break）"""


def fin_continue(rows):
    out = []
    for r in rows:
        try:
            if r < 0:
                raise ValueError(r)
        finally:
            if r < 0:
                continue
        out.append(r)
    return out


def fin_break(rows):
    total = 0
    for r in rows:
        try:
            total += r
        finally:
            if total > 100:
                break
    return total


def fin_continue_stmt(rows):
    out = []
    i = 0
    while i < len(rows):
        try:
            v = rows[i]
        finally:
            i += 1
            if v is None:
                continue
        out.append(v)
    return out
'''

# 逐字复刻 adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.py
REPL['l0_d4_repl_v_b71_face.py'] = '''"""逐字复刻 v_b71_face（B142 登记残余所在文件）"""


def v_fin_else_continue(rows):
    out = []
    for r in rows:
        try:
            if r < 0:
                raise ValueError(r)
        finally:
            if r < 0:
                continue
            else:
                out.append(-r)
        out.append(r)
    return out


def v_nest_fin_continue(rows):
    out = []
    for r in rows:
        try:
            try:
                if r == 0:
                    continue
            finally:
                out.append(1)
        finally:
            out.append(2)
        out.append(r)
    return out


def n_fin_noctrl(rows):
    out = []
    for r in rows:
        try:
            if r < 0:
                raise ValueError(r)
        finally:
            if r < 0:
                out.append(-r)
        out.append(r)
    return out
'''


def main():
    os.makedirs(PROBES, exist_ok=True)
    for name, src in sorted(REPL.items()):
        with open(os.path.join(PROBES, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write(src)
        print('wrote %s' % name)
    return 0


if __name__ == '__main__':
    sys.exit(main())
