#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：**独立复跑**关键读数（不依赖已落盘的汇总，直接走约定命令形式）。

与 `_scripts/mutation_experiment.py` 的区别：
  * 本脚本**只用 CLI 子进程**（`python -X utf8 scripts/pyc_verify.py single <pyc> --source <product>`）
    复判，不走 `evaluate()` 内部 API ⇒ 验证的是**约定命令本身**的判定；
  * 每次复判都先跑一次**未变异的原产物**作基线（必须仍为 success ⇒ 前提成立）；
  * 只复跑 6 个「证据锚点」读数（本报告 §0.2 的 E1/E2/E3 + 2 个对照捕获），
    不重跑全量变异（全量由 mutation_experiment.py / mutation_summary.py 负责）。

输出：`_out/verify_l2_readings.json`（逐例：命令 / status / 判定）。
用法：python -X utf8 verify_l2_readings.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND4 = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(ROUND4, '..', '..', '..', '..', '..'))
OUT = os.path.join(ROUND4, '_out')

sys.path.insert(0, HERE)
import mutation_lib  # noqa: E402

# 语料级锚点：(标签, pyc 相对路径, 产物相对路径, 变异族)
CORPUS_CASES = [
    ('E1-值类型 x=1->x=True', r'site-packages\IQCommon\api\gtn_api.pyc',
     r'site-packages\IQCommon\api\gtn_apiOK.py', 'd_int_to_bool'),
    ('E1b-值精度 x=1->x=1.0', r'site-packages\IQCommon\api\gtn_api.pyc',
     r'site-packages\IQCommon\api\gtn_apiOK.py', 'i_int_to_float'),
    ('E2-形参换序', r'site-packages\IQCommon\api\gtn_api.pyc',
     r'site-packages\IQCommon\api\gtn_apiOK.py', 'h_param_order'),
    ('对照A-删赋值(应捕获)', r'site-packages\IQCommon\api\gtn_api.pyc',
     r'site-packages\IQCommon\api\gtn_apiOK.py', 'c_del_assign'),
    ('对照B-比较极性反转(应捕获)', r'site-packages\IQCommon\api\gtn_api.pyc',
     r'site-packages\IQCommon\api\gtn_apiOK.py', 'b_cmp_polarity'),
    ('函数docstring', r'site-packages\IQCommon\api\gtn_api.pyc',
     r'site-packages\IQCommon\api\gtn_apiOK.py', 'j_func_docstring'),
]

# 构造级锚点（E3 对照实验）：(标签, 探针名, 变异产物名, 期望)
PROBE_CASES = [
    ('E3a-空try体改handler体(期望漏检)', 'cp_try_pass_handler_body',
     'cp_try_pass_handler_body_mut.py', 'MISS'),
    ('E3b-空try体改except类型(期望漏检)', 'cp_try_pass_except_type',
     'cp_try_pass_except_type_mut.py', 'MISS'),
    ('E3c-对照:try体有赋值改handler体(期望捕获)', 'cp_try_assign_handler_body',
     'cp_try_assign_handler_body_mut.py', 'CAUGHT'),
    ('E3d-对照:try体raise改handler体(期望捕获)', 'cp_try_raise_handler_body',
     'cp_try_raise_handler_body_mut.py', 'CAUGHT'),
    ('E3e-except元组换序(期望漏检)', 'cp_except_tuple_order',
     'cp_except_tuple_order_mut.py', 'MISS'),
    ('对照F-函数docstring(期望漏检)', 'cp_docstring_func',
     'cp_docstring_func_mut.py', 'MISS'),
]

STATUS_RE = re.compile(r'\[single\] status=(\w+) units=(\d+)/(\d+)')


def run_single(pyc: str, source: str) -> dict:
    cmd = [sys.executable, '-X', 'utf8', os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
           'single', pyc, '--source', source]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          encoding='utf-8', errors='replace', timeout=280)
    out = (proc.stdout or '') + (proc.stderr or '')
    m = STATUS_RE.search(out)
    status = m.group(1) if m else 'no_status'
    units = [int(m.group(2)), int(m.group(3))] if m else [0, 0]
    verdict = 'MISS' if status == 'success' else (
        'CAUGHT' if status == 'failure' else status.upper())
    return {'command': ' '.join(cmd[1:]), 'rc': proc.returncode, 'status': status,
            'units': units, 'verdict': verdict,
            'stdout_tail': out.strip().splitlines()[-3:]}


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    rows = []
    tmp = tempfile.mkdtemp(prefix='l2verify_')

    # ── 语料级：原产物基线 + 变异体复判 ────────────────────────────────
    for label, pyc_rel, prod_rel, fam in CORPUS_CASES:
        pyc = os.path.join(ROOT, pyc_rel)
        prod = os.path.join(ROOT, prod_rel)
        if not (os.path.isfile(pyc) and os.path.isfile(prod)):
            rows.append({'label': label, 'family': fam, 'skipped': 'corpus missing'})
            continue
        base = run_single(pyc, prod)
        raw = open(prod, 'rb').read()
        mut, site = mutation_lib.apply_mutation(fam, raw)
        if mut is None:
            rows.append({'label': label, 'family': fam, 'baseline': base,
                         'skipped': 'family NA on this product'})
            continue
        mpath = os.path.join(tmp, 'v_%s.py' % fam)
        with open(mpath, 'wb') as f:
            f.write(mut)
        mut_row = run_single(pyc, mpath)
        rows.append({'label': label, 'family': fam, 'pyc': pyc_rel.replace('\\', '/'),
                     'baseline': base, 'mutant': mut_row, 'site': site,
                     'mutant_file': 'tmp:' + os.path.basename(mpath)})

    # ── 构造级：探针原产物基线 + 已落盘变异体复判 ─────────────────────
    pdir = os.path.join(ROUND4, '_probes')
    mdir = os.path.join(pdir, 'mut')
    for label, probe, mutname, expect in PROBE_CASES:
        pyc = os.path.join(pdir, probe + '.pyc')
        prod = os.path.join(pdir, probe + 'OK.py')
        mutf = os.path.join(mdir, mutname)
        if not (os.path.isfile(pyc) and os.path.isfile(prod) and os.path.isfile(mutf)):
            rows.append({'label': label, 'skipped': 'probe artifacts missing'})
            continue
        base = run_single(pyc, prod)
        mut_row = run_single(pyc, mutf)
        rows.append({'label': label, 'probe': probe, 'expected': expect,
                     'baseline': base, 'mutant': mut_row,
                     'consistent': (mut_row['verdict'] == expect)})

    data = {'rows': rows,
            'summary': {
                'cases': len(rows),
                'miss': sum(1 for r in rows if r.get('mutant', {}).get('verdict') == 'MISS'),
                'caught': sum(1 for r in rows if r.get('mutant', {}).get('verdict') == 'CAUGHT'),
                'skipped': sum(1 for r in rows if 'skipped' in r),
                'consistent_with_expectation': sum(1 for r in rows if r.get('consistent')),
            }}
    path = os.path.join(OUT, 'verify_l2_readings.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    for r in rows:
        if 'skipped' in r:
            print('[SKIP] %-46s %s' % (r['label'], r['skipped']))
            continue
        print('[%-6s] %-46s base=%s mutant=%s units=%s%s' % (
            r['mutant']['verdict'], r['label'],
            r['baseline']['status'], r['mutant']['status'],
            r['mutant']['units'],
            ('  expected=%s' % r['expected']) if 'expected' in r else ''))
    print('[summary] %s' % json.dumps(data['summary'], ensure_ascii=False))
    print('[out] %s' % path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
