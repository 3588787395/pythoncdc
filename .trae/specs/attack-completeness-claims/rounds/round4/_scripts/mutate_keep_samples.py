#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：**按留存规则重建漏检样本**（不重判，只重建变异体）。

从 `_out/mutate_results.jsonl` 里挑出每族最多 3 条漏检记录，
用 `_scripts/mutation_lib.py` 重新注入同一语义错误，落盘到
`_probes/miss_cli/miss_<md5(pyc|family)[:16]>_<family>.py`。

命名与 `mutate.py` 完全一致 ⇒ 与 CLI 口径的逐次记录一一对应。

用法：
  python -X utf8 mutate_keep_samples.py [--per-family 3]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND4 = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(ROUND4, '..', '..', '..', '..', '..'))
OUT = os.path.join(ROUND4, '_out')
RESULTS = os.path.join(OUT, 'mutate_results.jsonl')
MISS_DIR = os.path.join(ROUND4, '_probes', 'miss_cli')

sys.path.insert(0, HERE)
import mutation_lib  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--per-family', type=int, default=3)
    ap.add_argument('--results', default=RESULTS)
    ap.add_argument('--out-dir', default=MISS_DIR)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    misses = []
    for line in open(args.results, encoding='utf-8'):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get('family') == 'BASELINE':
            continue
        if r.get('status') == 'success':
            misses.append(r)
    misses.sort(key=lambda r: (r['family'], r['pyc']))

    kept = {}
    for r in misses:
        fam = r['family']
        if kept.get(fam, 0) >= args.per_family:
            continue
        prod = r['pyc'][:-4] + 'OK.py'
        if not os.path.isfile(prod):
            continue
        raw = open(prod, 'rb').read()
        mut, site = mutation_lib.apply_mutation(fam, raw)
        if mut is None:
            continue
        dg = hashlib.md5(('%s|%s' % (r['pyc'], fam)).encode('utf-8')).hexdigest()[:16]
        dst = os.path.join(args.out_dir, 'miss_%s_%s.py' % (dg, fam))
        with open(dst, 'wb') as f:
            f.write(mut)
        kept[fam] = kept.get(fam, 0) + 1
    print('kept per family: %s -> %s' % (kept, args.out_dir))
    return 0


if __name__ == '__main__':
    sys.exit(main())
