#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round4 复核（Task 4.3）：独立复跑攻击驱动（RV2：compile -> pycdc regen -> pyc_verify batch）。

复核人自建；只跑本轮 25 个自有探针（c4_01..c4_20 + n4_01_neg..n4_05），
排除 round4 预置 tracked 文件（n4_01_no_match_control、r4_*、rv4_*、probe_*）。
输出 r4v4r_ 前缀证据；逐单元对照上一批 r4v4_probe_full.json 判定 NEWFAIL。
只读 core/，禁止覆盖 r4v4_* / round3 证据。
"""
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

STEMS = ['c4_%02d_%s' % (i, s) for i, s in [
    (1, 'elif_chain'), (2, 'loop_else'), (3, 'except_star'), (4, 'match_patterns'),
    (5, 'multi_with'), (6, 'try_finally_only'), (7, 'multi_target'), (8, 'augassign'),
    (9, 'chained_compare'), (10, 'walrus'), (11, 'keyword_args'), (12, 'star_args'),
    (13, 'slice'), (14, 'relative_import'), (15, 'star_import'), (16, 'global_nonlocal'),
    (17, 'fstring_conv'), (18, 'nested_comprehension'), (19, 'decorator_args'),
    (20, 'async_five')]] + [
    'n4_01_neg_control_flow', 'n4_02_neg_expr', 'n4_03_neg_match_with',
    'n4_04_neg_deco_async', 'n4_05_neg_except_star']


def run(cmd, timeout=290):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -9, 'TIMEOUT'


def main():
    index = []
    for stem in STEMS:
        src = os.path.join(R4, stem + '.py')
        pyc = os.path.join(R4, stem + '.pyc')
        rc, out = run([sys.executable, '-c',
                       'import py_compile,sys; py_compile.compile(sys.argv[1], sys.argv[2], doraise=True, optimize=0)',
                       src, pyc])
        if rc != 0:
            print('COMPILE FAIL(src)', stem, out.strip()[-200:])
            continue
        ok = os.path.join(R4, stem + 'OK.py')
        run([sys.executable, os.path.join(ROOT, 'pycdc.py'), pyc, '-o', ok])
        index.append({'path': 'test_repros/round4/%s.pyc' % stem})

    idx_path = os.path.join(HERE, 'r4v4r_probe_index.json')
    with open(idx_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    print('index -> %s (%d files)' % (idx_path, len(index)))

    rep_path = os.path.join(HERE, 'r4v4r_probe_results.json')
    rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                   'batch', '--index', idx_path, '--json', rep_path])
    print('batch rc=%d' % rc)

    rows = []
    for stem in STEMS:
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
        print('%-13s %s/%s %s' % (status, us, ut, stem), flush=True)
    full_path = os.path.join(HERE, 'r4v4r_probe_full.json')
    with open(full_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    tok = sum(r['units_success'] or 0 for r in rows)
    tot = sum(r['units_total'] or 0 for r in rows)
    print('-> %s  probe units=%d/%d' % (full_path, tok, tot))


if __name__ == '__main__':
    main()