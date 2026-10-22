#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：**独立复跑**（只用约定 CLI 命令，不用任何已落盘的汇总读数）。

对每一例（判据该抓的 / 该漏的），从**产物**重新注入同一语义错误，重新落盘，
然后原样执行：

    python -X utf8 scripts/pyc_verify.py single <pyc> --source <变异产物>

把 CLI 打印的 `[single] status=... units=...` 原样记录下来，与期望（MISS/CAUGHT）比对。

用法：
  python -X utf8 mutate_recheck.py [--out _out/mutate_recheck.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND4 = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(ROUND4, '..', '..', '..', '..', '..'))
OUT = os.path.join(ROUND4, '_out')
RESULTS = os.path.join(OUT, 'mutate_results.jsonl')
SCRATCH = os.path.join(ROUND4, '_scratch', 'recheck')

sys.path.insert(0, HERE)
import mutation_lib  # noqa: E402

STATUS_RE = re.compile(r'\[single\]\s+status=(\w+)\s+units=(\d+)/(\d+)')

# 复跑清单：(family, 期望, 取第几条该族样例)
CASES = [
    ('d_int_to_bool', 'MISS', 0),
    ('d_int_to_bool', 'MISS', 1),
    ('d_int_to_bool', 'CAUGHT', 0),      # 该族唯一被抓的样例（对照）
    ('j_func_docstring', 'MISS', 0),
    ('h_param_order', 'MISS', 0),
    ('h_param_order', 'CAUGHT', 0),     # 对照
    ('e_str_content', 'MISS', 0),
    ('g_rename_local', 'MISS', 0),
    ('g3_kwparam_rename', 'CAUGHT', 0),  # 保证语义的对照组：必须抓到
    ('a_num_int', 'CAUGHT', 0),          # 对照组
    ('b_cmp_polarity', 'CAUGHT', 0),     # 对照组
    ('c_del_assign', 'CAUGHT', 0),       # 对照组
    ('f_stmt_swap', 'CAUGHT', 0),        # 对照组
    ('h_arg_swap', 'CAUGHT', 0),         # 对照组
]


def load_rows():
    rows = []
    for line in open(RESULTS, encoding='utf-8'):
        try:
            r = json.loads(line)
        except Exception:
            continue
        rows.append(r)
    return rows


def pick(rows, family, expect):
    """挑一条该族样例：MISS ⇒ status==success 的；CAUGHT ⇒ status==failure 的。"""
    want = 'success' if expect == 'MISS' else 'failure'
    for r in rows:
        if r['family'] == family and r.get('status') == want:
            return r
    return None


def run_cli(pyc, source):
    cmd = [sys.executable, '-X', 'utf8', os.path.join('scripts', 'pyc_verify.py'),
           'single', pyc, '--source', source]
    t0 = time.time()
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=180)
    out = (p.stdout or '') + (p.stderr or '')
    m = STATUS_RE.search(out)
    el = round(time.time() - t0, 2)
    if not m:
        return {'status': 'NO_STATUS', 'units': None, 'elapsed': el,
                'stdout_tail': out.strip()[-200:]}
    return {'status': m.group(1), 'units': '%s/%s' % (m.group(2), m.group(3)),
            'elapsed': el, 'stdout_tail': ''}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(OUT, 'mutate_recheck.json'))
    args = ap.parse_args()
    os.makedirs(SCRATCH, exist_ok=True)
    rows = load_rows()
    recs = []
    for family, expect, idx in CASES:
        r = pick(rows, family, expect)
        if r is None:
            recs.append({'family': family, 'expect': expect, 'result': 'NO_SAMPLE'})
            continue
        prod = r['pyc'][:-4] + 'OK.py'
        if not os.path.isfile(prod):
            recs.append({'family': family, 'expect': expect, 'result': 'NO_PRODUCT'})
            continue
        raw = open(prod, 'rb').read()
        mut, site = mutation_lib.apply_mutation(family, raw)
        if mut is None:
            recs.append({'family': family, 'expect': expect, 'result': 'NOT_REPRODUCIBLE'})
            continue
        dg = hashlib.md5(('%s|%s' % (r['pyc'], family)).encode('utf-8')).hexdigest()[:16]
        mp = os.path.join(SCRATCH, 'rc_%s_%s.py' % (dg, family))
        with open(mp, 'wb') as f:
            f.write(mut)
        out = run_cli(r['pyc'], mp)
        got = 'MISS' if out['status'] == 'success' else (
            'CAUGHT' if out['status'] == 'failure' else out['status'])
        recs.append({'family': family, 'expect': expect, 'got': got,
                     'status': out['status'], 'units': out['units'],
                     'elapsed': out['elapsed'],
                     'pyc': os.path.relpath(r['pyc'], ROOT).replace('\\', '/'),
                     'mutated': os.path.relpath(mp, ROOT).replace('\\', '/'),
                     'site': site,
                     'consistent': (got == expect)})
        print('%-18s expect=%-6s got=%-6s status=%-8s units=%-8s %s'
              % (family, expect, got, out['status'], out['units'],
                 'OK' if got == expect else 'MISMATCH'))
    summary = {'judge_command': 'python -X utf8 scripts/pyc_verify.py single <pyc> --source <mutated>',
               'cases': recs,
               'n_cases': len(recs),
               'n_consistent': sum(1 for r in recs if r.get('consistent')),
               'n_miss': sum(1 for r in recs if r.get('got') == 'MISS'),
               'n_caught': sum(1 for r in recs if r.get('got') == 'CAUGHT')}
    with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + '\n')
    print('cases=%d consistent=%d MISS=%d CAUGHT=%d -> %s'
          % (summary['n_cases'], summary['n_consistent'], summary['n_miss'],
             summary['n_caught'], args.out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
