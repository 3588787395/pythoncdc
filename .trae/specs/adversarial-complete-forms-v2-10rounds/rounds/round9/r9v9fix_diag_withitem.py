#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 续作 B124 诊断3：with-item 装配点 reconstruct 结果对照（merged vs v2gen 两臂）。

插桩点 = _generate_with 的 `expr = self.expr_reconstructor.reconstruct(...)` 前后。
臂 = control（合并树）| v2gen（91f8d27d 的 region_ast_generator.py + 同插桩）。
证据 → r9v9fix_diag_withitem.txt。
"""
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
GEN = os.path.join(ROOT, 'core', 'cfg', 'region_ast_generator.py')
BAKDIR = r'D:\Temp\opencode\r92bak2'
LOG = os.path.join(HERE, 'r9v9fix_diag_withitem.txt')
V2_COMMIT = '91f8d27d'

A1_OLD = ("                        expr = self.expr_reconstructor.reconstruct"
          "(expr_instrs) if expr_instrs else None\r\n")
A1_OLD_LF = A1_OLD.replace('\r\n', '\n')
A1_NEW = ("                        _t_ops = [i.opname for i in expr_instrs]\r\n"
          "                        import sys as _t_sys\r\n"
          "                        print('[I] item reconstruct ops=%s' % (_t_ops[:14],), file=_t_sys.stderr)\r\n"
          "                        expr = self.expr_reconstructor.reconstruct(expr_instrs) if expr_instrs else None\r\n"
          "                        print('[I] item reconstruct -> %s' % (expr and expr.get('type'),), file=_t_sys.stderr)\r\n")
A1_NEW_LF = A1_NEW.replace('\r\n', '\n')


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def instrument(text):
    for old, new in ((A1_OLD, A1_NEW), (A1_OLD_LF, A1_NEW_LF)):
        if text.count(old) == 1:
            return text.replace(old, new)
    raise AssertionError('anchor not found uniquely')


def main():
    arm = sys.argv[1]
    os.makedirs(BAKDIR, exist_ok=True)
    base = sha(GEN)
    orig = open(GEN, 'rb').read()
    with open(os.path.join(BAKDIR, 'region_ast_generator.py'), 'wb') as g:
        g.write(orig)
    try:
        if arm == 'v2gen':
            p = subprocess.run(['git', 'show', '%s:core/cfg/region_ast_generator.py' % V2_COMMIT],
                               capture_output=True, cwd=ROOT)
            assert p.returncode == 0 and p.stdout
            src = p.stdout.decode('utf-8')
        else:
            src = orig.decode('utf-8')
        with open(GEN, 'wb') as f:
            f.write(instrument(src).encode('utf-8'))
        out_lines = ['=== arm: %s ===' % arm]
        pr = subprocess.run([sys.executable, os.path.join(ROOT, 'pycdc.py'),
                             os.path.join(ROOT, 'test_repros', 'round8', 'r8_10_expr_cross_stmt.pyc'),
                             '-o', r'D:\Temp\opencode\r92_products\r8_10_%s.py' % arm],
                            capture_output=True, text=True, cwd=ROOT, timeout=250,
                            encoding='utf-8', errors='replace')
        out_lines += [l for l in ((pr.stdout or '') + (pr.stderr or '')).splitlines()
                      if '[I]' in l]
        with open(LOG, 'a', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out_lines) + '\n')
        print('\n'.join(out_lines[:30]))
    finally:
        with open(os.path.join(BAKDIR, 'region_ast_generator.py'), 'rb') as f:
            data = f.read()
        with open(GEN, 'wb') as f:
            f.write(data)
        assert sha(GEN) == base, 'RESTORE FAILED'
        print('-> restored OK')


if __name__ == '__main__':
    main()
