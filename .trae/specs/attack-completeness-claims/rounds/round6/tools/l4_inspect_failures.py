#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 失败样本取证：把判据失败单元、产物编译错误原因打印出来。

用法：python l4_inspect_failures.py <slug> [...]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND6 = os.path.dirname(HERE)
LOGS = os.path.join(ROUND6, 'logs')


def load_rows():
    rows = {}
    import glob
    for p in sorted(glob.glob(os.path.join(LOGS, 'l4_diff_part*.json'))):
        for r in json.load(open(p, encoding='utf-8'))['rows']:
            rows[r['slug']] = r
    return rows


def compile_error_detail(product: str) -> str:
    import py_compile
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        try:
            py_compile.compile(product, cfile=os.path.join(td, 'x.pyc'), doraise=True)
            return ''
        except py_compile.PyCompileError as exc:
            return str(exc).strip()[:1200]
        except Exception as exc:
            return '%s: %s' % (type(exc).__name__, exc)


def main() -> int:
    rows = load_rows()
    slugs = sys.argv[1:]
    if not slugs:
        slugs = sorted(rows)
    for slug in slugs:
        r = rows[slug]
        v = r.get('verify', {})
        print('=' * 100)
        print('[%s] status=%s units=%s/%s origin=%s' % (
            slug, v.get('status'), v.get('units_success'), v.get('units_total'), r.get('origin')))
        print('  src      : %s' % r.get('src'))
        print('  pyc      : %s' % r.get('pyc_src'))
        print('  product  : %s (%s bytes)' % (r.get('product'),
                                            os.path.getsize(r['product']) if os.path.exists(r.get('product', '')) else -1))
        if r.get('src_matches_pyc') is False:
            print('  !! src != pyc （源码已被改动过，语义核对须以 pyc 为准）')
        if v.get('status') == 'compile_error':
            print('  --- compile_error detail ---')
            print(compile_error_detail(r['product']))
            continue
        for f in (v.get('failures') or [])[:40]:
            print('  FAIL %s' % f)
    return 0


if __name__ == '__main__':
    sys.exit(main())
