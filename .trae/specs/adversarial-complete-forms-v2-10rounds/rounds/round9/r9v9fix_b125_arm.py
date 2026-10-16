#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 续作 B125 对照臂：关 [B125-R1] 祖先链排除后重跑 w16_05 / r6_q2_spec（只读，还原）。"""
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
GEN = os.path.join(ROOT, 'core', 'cfg', 'region_ast_generator.py')
BAKDIR = r'D:\Temp\opencode\r92bak2'
TMPOUT = r'D:\Temp\opencode\r92_products'

A_OLD = ("            _r125_ancestor_ids = set()\r\n"
         "            _r125_anc = getattr(region, 'parent', None)\r\n"
         "            while _r125_anc is not None:\r\n"
         "                _r125_ancestor_ids.add(id(_r125_anc))\r\n"
         "                _r125_anc = getattr(_r125_anc, 'parent', None)\r\n"
         "            for _r in self.regions:\r\n"
         "                if _r is region or id(_r) in _r125_ancestor_ids:\r\n")
A_NEW = ("            _r125_ancestor_ids = set()\r\n"
         "            for _r in self.regions:\r\n"
         "                if _r is region:\r\n")

PROBES = [
    ('w16_05_nested_in_for', 'test_repros/round9/r9w16_05_nested_in_for.py'),
    ('r6_q2_whilehost_spec', 'test_repros/round6/r6_q2_whilehost_spec.py'),
    ('r9w16_17_else_nested_loop', 'test_repros/round9/r9w16_17_ctl_else_nested_loop.py'),
]


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def run(cmd, timeout=200):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return 'TIMEOUT'


def probe(name, src):
    pyc = os.path.join(TMPOUT, 'b125_' + name + '_src.pyc')
    ok = os.path.join(TMPOUT, 'b125_' + name + '_off.py')
    subprocess.run([sys.executable, '-c',
                   'import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], doraise=True)',
                   os.path.join(ROOT, src.replace('/', os.sep)), pyc], check=True)
    run([sys.executable, os.path.join(ROOT, 'pycdc.py'), pyc, '-o', ok])
    out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
               'single', pyc, '--source', ok])
    import re
    status = us = ut = None
    m = re.search(r'status=(\w+)\s+units=(\d+)/(\d+)', out)
    if m:
        status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
    fails = [l.strip() for l in out.splitlines() if 'Failure' in l]
    return status, us, ut, fails, ok


def main():
    os.makedirs(BAKDIR, exist_ok=True)
    base = sha(GEN)
    orig = open(GEN, 'rb').read()
    with open(os.path.join(BAKDIR, 'region_ast_generator.py'), 'wb') as g:
        g.write(orig)
    try:
        text = orig.decode('utf-8')
        assert text.count(A_OLD) == 1
        with open(GEN, 'wb') as f:
            f.write(text.replace(A_OLD, A_NEW).encode('utf-8'))
        for name, src in PROBES:
            status, us, ut, fails, ok = probe(name, src)
            print('[off-B125R1 %-22s] %-8s %s/%s fails=%s' % (name, status, us, ut, fails[:2]),
                  flush=True)
    finally:
        with open(os.path.join(BAKDIR, 'region_ast_generator.py'), 'rb') as f:
            data = f.read()
        with open(GEN, 'wb') as f:
            f.write(data)
        assert sha(GEN) == base, 'RESTORE FAILED'
        print('-> restored OK')


if __name__ == '__main__':
    main()
