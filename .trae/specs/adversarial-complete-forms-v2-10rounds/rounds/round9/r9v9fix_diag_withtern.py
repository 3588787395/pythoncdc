#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 续作 B124 诊断2：merged gen `_resolve_nested_ternary_context_expr` 在 r8_x_with_ternary 的回退点。"""
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
GEN = os.path.join(ROOT, 'core', 'cfg', 'region_ast_generator.py')
BAKDIR = r'D:\Temp\opencode\r92bak2'
LOG = os.path.join(HERE, 'r9v9fix_diag_withtern.txt')

A1 = ("        _fallback = {'type': 'Call', 'func': {'type': 'Name', 'id': 'context'},\r\n"
      "                     'args': [], 'keywords': []}\r\n"
      "        if with_region.entry is None:\r\n"
      "            return _fallback, []\r\n",
      "        _fallback = {'type': 'Call', 'func': {'type': 'Name', 'id': 'context'},\r\n"
      "                     'args': [], 'keywords': []}\r\n"
      "        import sys as _t_sys\r\n"
      "        print('[W] resolve enter with_entry=%s' % (with_region.entry.start_offset), file=_t_sys.stderr)\r\n"
      "        if with_region.entry is None:\r\n"
      "            return _fallback, []\r\n")
A2 = ("        if _nested_ternary is None:\r\n"
      "            return _fallback, []\r\n",
      "        if _nested_ternary is None:\r\n"
      "            print('[W] nested ternary NOT FOUND', file=_t_sys.stderr)\r\n"
      "            return _fallback, []\r\n")
A3 = ("        if not _t_stmts:\r\n"
      "            return _fallback, []\r\n",
      "        if not _t_stmts:\r\n"
      "            print('[W] _generate_ternary empty', file=_t_sys.stderr)\r\n"
      "            return _fallback, []\r\n")
A4 = ("        if _t_expr is None:\r\n"
      "            return _fallback, []\r\n",
      "        if _t_expr is None:\r\n"
      "            print('[W] t_node type=%s stmts=%s' % (_t_node.get('type'), [s.get('type') for s in _t_stmts]), file=_t_sys.stderr)\r\n"
      "            return _fallback, []\r\n")


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def main():
    os.makedirs(BAKDIR, exist_ok=True)
    base = sha(GEN)
    orig = open(GEN, 'rb').read()
    with open(os.path.join(BAKDIR, 'region_ast_generator.py'), 'wb') as g:
        g.write(orig)
    text = orig.decode('utf-8')
    for old, new in (A1, A2, A3, A4):
        assert text.count(old) == 1, 'anchor x%d: %r' % (text.count(old), old[:60])
        text = text.replace(old, new)
    try:
        with open(GEN, 'wb') as f:
            f.write(text.encode('utf-8'))
        out_lines = []
        p = subprocess.run([sys.executable, os.path.join(ROOT, 'pycdc.py'),
                            os.path.join(ROOT, 'test_repros', 'round8', 'r8_10_expr_cross_stmt.pyc'),
                            '-o', r'D:\Temp\opencode\r92_products\r8_10_withtern.py'],
                           capture_output=True, text=True, cwd=ROOT, timeout=250,
                           encoding='utf-8', errors='replace')
        out_lines += [l for l in ((p.stdout or '') + (p.stderr or '')).splitlines()
                      if '[W]' in l]
        open(LOG, 'w', encoding='utf-8', newline='\n').write('\n'.join(out_lines))
        print('\n'.join(out_lines[:40]))
    finally:
        with open(os.path.join(BAKDIR, 'region_ast_generator.py'), 'rb') as f:
            data = f.read()
        with open(GEN, 'wb') as f:
            f.write(data)
        assert sha(GEN) == base, 'RESTORE FAILED'
        print('-> restored OK')


if __name__ == '__main__':
    main()
