#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 续作 B124 生成器桶诊断：ma_v2g 臂（merged ana + v2 gen）产物 dump（只读，结束还原）。"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
ANA = os.path.join(ROOT, 'core', 'cfg', 'region_analyzer.py')
GEN = os.path.join(ROOT, 'core', 'cfg', 'region_ast_generator.py')
BAKDIR = r'D:\Temp\opencode\r92bak2'
TMPOUT = r'D:\Temp\opencode\r92_products'
V2_COMMIT = '91f8d27d'


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def run(cmd, timeout=250):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return 'TIMEOUT'


def main():
    os.makedirs(BAKDIR, exist_ok=True)
    base = {}
    for name in ('region_analyzer.py', 'region_ast_generator.py'):
        src = os.path.join(ROOT, 'core', 'cfg', name)
        with open(src, 'rb') as f:
            data = f.read()
        base[name] = sha(src)
        with open(os.path.join(BAKDIR, name), 'wb') as g:
            g.write(data)
    try:
        p = subprocess.run(['git', 'show', '%s:core/cfg/region_ast_generator.py' % V2_COMMIT],
                           capture_output=True, cwd=ROOT)
        assert p.returncode == 0 and p.stdout
        with open(GEN, 'wb') as f:
            f.write(p.stdout)
        print('v2 gen in place: sha16=%s' % hashlib.sha256(p.stdout).hexdigest()[:16])
        for name, rel in [('e10', 'test_repros/round3/e10_g7_call_args.pyc'),
                          ('r8_10', 'test_repros/round8/r8_10_expr_cross_stmt.pyc')]:
            full = os.path.join(ROOT, rel.replace('/', os.sep))
            ok = os.path.join(TMPOUT, name + '_ma_v2g.py')
            run([sys.executable, os.path.join(ROOT, 'pycdc.py'), full, '-o', ok])
            out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                       'single', full, '--source', ok])
            print('[ma_v2g %s] %s' % (name, [l for l in out.splitlines()
                                             if 'status=' in l]), flush=True)
    finally:
        for name in ('region_analyzer.py', 'region_ast_generator.py'):
            with open(os.path.join(BAKDIR, name), 'rb') as f:
                data = f.read()
            with open(os.path.join(ROOT, 'core', 'cfg', name), 'wb') as f:
                f.write(data)
            assert sha(os.path.join(ROOT, 'core', 'cfg', name)) == base[name], name
        print('-> restored OK')


if __name__ == '__main__':
    main()
