#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 4（表C 31 扩展形态对抗）探针攻击驱动（RV2：compile -> pycdc regen -> pyc_verify batch）。

只读 core/，只写 test_repros/round4 探针产物与本目录 r4v4_* 证据 JSON。
"""
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
R4 = os.path.join(ROOT, 'test_repros', 'round4')
STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')


def run(cmd, timeout=290):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -9, 'TIMEOUT'


def main():
    stems = []
    for p in sorted(glob.glob(os.path.join(R4, 'c4_*.py')) + glob.glob(os.path.join(R4, 'n4_*.py'))):
        if p.endswith('OK.py'):
            continue
        stems.append(os.path.splitext(os.path.basename(p))[0])

    index = []
    for stem in stems:
        src = os.path.join(R4, stem + '.py')
        pyc = os.path.join(R4, stem + '.pyc')
        rc, out = run([sys.executable, '-c',
                       'import py_compile,sys; py_compile.compile(sys.argv[1], sys.argv[2], doraise=True, optimize=0)',
                       src, pyc])
        if rc != 0:
            print('COMPILE FAIL(src)', stem, out.strip()[-200:])
            continue
        ok = os.path.join(R4, stem + 'OK.py')
        rc, out = run([sys.executable, os.path.join(ROOT, 'pycdc.py'), pyc, '-o', ok])
        if rc != 0:
            print('PYCDC FAIL', stem, out.strip()[-200:])
        index.append({'path': 'test_repros/round4/%s.pyc' % stem})

    idx_path = os.path.join(HERE, 'r4v4_probe_index.json')
    with open(idx_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    print('index -> %s (%d files)' % (idx_path, len(index)))

    rep_path = os.path.join(HERE, 'r4v4_probe_results.json')
    rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                   'batch', '--index', idx_path, '--json', rep_path])
    print('batch rc=%d' % rc)
    print('\n'.join(out.strip().splitlines()[-8:]))

    # 逐文件完整输出（含失败单元名），供 §3 失败要点引用
    rows = []
    for stem in stems:
        pyc = os.path.join(R4, stem + '.pyc')
        if not os.path.isfile(pyc):
            continue
        rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'), 'single', pyc])
        status, us, ut = None, None, None
        fails = []
        for line in out.splitlines():
            m = STAT_RE.search(line)
            if m:
                status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
            if FAIL_RE.match(line):
                fails.append(line.strip())
        rows.append({'pyc': 'test_repros/round4/%s.pyc' % stem, 'verify_rc': rc,
                     'status': status, 'units_success': us, 'units_total': ut, 'failures': fails})
        print('%-9s %s/%s %s' % (status, us, ut, stem), flush=True)
    full_path = os.path.join(HERE, 'r4v4_probe_full.json')
    with open(full_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    tok = sum(r['units_success'] or 0 for r in rows)
    tot = sum(r['units_total'] or 0 for r in rows)
    print('-> %s  probe units=%d/%d' % (full_path, tok, tot))


if __name__ == '__main__':
    main()