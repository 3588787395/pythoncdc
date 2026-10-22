#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 「源码 ≡ 原件 pyc」严格核对（co_code + co_consts + co_names）。

为什么必须严格：`l4_offcorpus_diff.py` 的 `source_matches_pyc` 只比 `co_code`，
**常量池不同也判 True**。实测本机 `D:\\Python\\Lib\\ipaddress.py`（磁盘源码）与
`__pycache__\\ipaddress.cpython-311.pyc` 的常量池不同（磁盘源码用 `%` 格式化，
pyc 用 f-string）⇒ 「读源码核对语义」必须先确认源码与 pyc 同源，否则会把
「系统升级导致的源码漂移」误记成「反编译器语义错」。

输出：logs/l4_src_pycheck.json
"""
from __future__ import annotations

import json
import marshal
import os
import py_compile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND6 = os.path.dirname(HERE)
LOGS = os.path.join(ROUND6, 'logs')
OFF = os.path.join(ROUND6, 'offcorpus')


def load_pyc_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def tree(code, prefix=''):
    """(qualname, co_code, co_consts, co_names) 递归表。"""
    out = [(prefix + code.co_name, code.co_code,
            tuple(repr(c) for c in code.co_consts if not hasattr(c, 'co_code')),
            code.co_names)]
    for c in code.co_consts:
        if hasattr(c, 'co_code'):
            out.extend(tree(c, prefix + code.co_name + '.'))
    return out


def main() -> int:
    samples = json.load(open(os.path.join(OFF, 'samples.json'), encoding='utf-8'))['samples']
    rows = []
    for s in samples:
        src, pyc = s['src'], s['pyc']
        rec = {'slug': s['slug'], 'src': src, 'pyc': pyc}
        try:
            orig = load_pyc_code(pyc)
            with tempfile.TemporaryDirectory() as td:
                cpath = os.path.join(td, 'x.pyc')
                py_compile.compile(src, cfile=cpath, doraise=True, optimize=0)
                recomp = load_pyc_code(cpath)
        except Exception as exc:
            rec['error'] = '%s: %s' % (type(exc).__name__, exc)
            rows.append(rec)
            continue
        a, b = tree(orig), tree(recomp)
        rec['code_equal'] = (len(a) == len(b) and
                             all(x[0] == y[0] and x[1] == y[1] for x, y in zip(a, b)))
        rec['consts_equal'] = (len(a) == len(b) and
                               all(x[0] == y[0] and x[2] == y[2] for x, y in zip(a, b)))
        rec['names_equal'] = (len(a) == len(b) and
                              all(x[0] == y[0] and x[3] == y[3] for x, y in zip(a, b)))
        rec['same_semantics'] = bool(rec['code_equal'] and rec['consts_equal'] and rec['names_equal'])
        if not rec['same_semantics']:
            # 找第一处常量差异，附上下文
            for x, y in zip(a, b):
                if x[0] == y[0] and x[2] != y[2]:
                    only_src = [c for c in x[2] if c not in y[2]][:4]
                    only_pyc = [c for c in y[2] if c not in x[2]][:4]
                    rec['first_const_diff'] = {'code': x[0],
                                               'only_in_src': only_src,
                                               'only_in_pyc': only_pyc}
                    break
        rows.append(rec)
    with open(os.path.join(LOGS, 'l4_src_pycheck.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'rows': rows}, f, ensure_ascii=False, indent=1)
    same = [r['slug'] for r in rows if r.get('same_semantics')]
    diff = [(r['slug'], r.get('code_equal'), r.get('consts_equal'), r.get('names_equal'))
            for r in rows if not r.get('same_semantics')]
    print('[src==pyc] same=%d/%d' % (len(same), len(rows)))
    for d in diff:
        print('   DIFF %-30s code=%s consts=%s names=%s' % d)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
