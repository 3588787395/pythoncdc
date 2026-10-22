#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 最小化复现件的最终取证（判据 + 执行级）。

对 repro/min_*.py：编译 → pycdc → pyc_verify → 执行原/产物并比对 stdout。
输出：logs/l4_min_eval.json
"""
from __future__ import annotations

import glob
import json
import os
import py_compile
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND6 = os.path.dirname(HERE)
LOGS = os.path.join(ROUND6, 'logs')
REPRO = os.path.join(ROUND6, 'repro')
REPO = os.path.abspath(os.path.join(ROUND6, '..', '..', '..', '..', '..'))

RUNNER = (
    "import importlib.util, sys\n"
    "spec = importlib.util.spec_from_file_location('m', sys.argv[1])\n"
    "m = importlib.util.module_from_spec(spec)\n"
    "sys.modules['m'] = m\n"
    "spec.loader.exec_module(m)\n"
    "m.main()\n"
)


def run(cmd, timeout=120):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                           errors='replace', timeout=timeout, cwd=REPO)
        return {'rc': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except subprocess.TimeoutExpired:
        return {'rc': None, 'stdout': '', 'stderr': 'TIMEOUT'}


def main() -> int:
    rows = []
    for py in sorted(glob.glob(os.path.join(REPRO, 'min_*.py'))):
        if py.endswith('OK.py'):
            continue
        base = py[:-3]
        pyc = base + '.pyc'
        prod = base + 'OK.py'
        if os.path.exists(prod):
            os.remove(prod)
        try:
            py_compile.compile(py, cfile=pyc, doraise=True)
        except Exception as exc:
            rows.append({'file': py, 'error': str(exc)})
            continue
        d = run([sys.executable, '-X', 'utf8', 'pycdc.py', pyc, '-o', prod])
        v = run([sys.executable, '-X', 'utf8', 'scripts/pyc_verify.py', 'single', pyc,
                 '--source', prod]) if os.path.exists(prod) else {'stdout': ''}
        status = None
        units = None
        for line in (v['stdout'] or '').splitlines():
            s = line.strip()
            if s.startswith('[single] status='):
                for part in s.split():
                    if part.startswith('status='):
                        status = part.split('=', 1)[1]
                    if part.startswith('units='):
                        units = part.split('=', 1)[1]
        s = run([sys.executable, '-X', 'utf8', '-c', RUNNER, py], timeout=40)
        o = run([sys.executable, '-X', 'utf8', '-c', RUNNER, prod], timeout=40) \
            if os.path.exists(prod) else {'rc': None, 'stdout': '', 'stderr': 'NO-PRODUCT'}
        rows.append({'file': py, 'pyc': pyc, 'product': prod,
                     'lines': len(open(py, encoding='utf-8').read().splitlines()),
                     'pycdc_rc': d['rc'], 'verify_status': status, 'verify_units': units,
                     'src_stdout': s['stdout'], 'prod_stdout': o['stdout'],
                     'src_rc': s['rc'], 'prod_rc': o['rc'],
                     'exec_equal': s['stdout'] == o['stdout'] and s['rc'] == o['rc'],
                     'prod_stderr_tail': (o.get('stderr') or '')[-300:]})
        print('[min-eval] %-28s lines=%d verify=%-12s exec_equal=%s' % (
            os.path.basename(py), rows[-1]['lines'], status, rows[-1]['exec_equal']))
        print('           src : %r' % s['stdout'][:100])
        print('           prod: %r %s' % (o['stdout'][:100], (o.get('stderr') or '')[-100:].replace('\n', ' ')))
    with open(os.path.join(LOGS, 'l4_min_eval.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'rows': rows}, f, ensure_ascii=False, indent=1)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
