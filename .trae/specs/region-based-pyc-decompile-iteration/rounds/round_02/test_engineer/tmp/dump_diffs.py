#!/usr/bin/env python3
"""批量导出 bad==1 文件的首个不一致点上下文（测试工程师临时工具）。

用法：
  D:/Python/python.exe dump_diffs.py --start 0 --end 12 --out part_a.txt
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))

import pyc_diff as pd  # noqa: E402

BASELINE = ROOT / '.trae/specs/region-based-pyc-decompile-iteration/rounds/round_02/baseline/batch_000.json'


def ok_path(pyc_path):
    p = Path(pyc_path)
    return str(p.with_suffix('')) + 'OK.py'


def load_targets(only_bad=1):
    d = json.load(open(BASELINE, encoding='utf-8'))
    rows = []
    for x in d['files']:
        bad = x.get('mismatches') or []
        if len(bad) == only_bad:
            rows.append((x['path'], bad[0]))
    rows.sort(key=lambda r: (r[1]['true_diffs'], r[1]['orig_count']))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--end', type=int, default=10 ** 9)
    ap.add_argument('--ctx', type=int, default=8)
    ap.add_argument('--out', required=True)
    ap.add_argument('--bad', type=int, default=1)
    args = ap.parse_args()

    rows = load_targets(args.bad)
    t0 = time.time()
    out = []
    for i, (pyc, m) in enumerate(rows):
        if i < args.start or i >= args.end:
            continue
        rel = pyc.replace(str(ROOT) + '/', '')
        okp = ok_path(pyc)
        out.append('=' * 100)
        out.append(f'[{i}] {rel}')
        out.append(f'    func={m["name"]} orig={m["orig_count"]} decomp={m["decomp_count"]} '
                   f'jump={m["jump_diffs"]} true={m["true_diffs"]}')
        fd = m.get('first_diff') or {}
        out.append(f'    first_diff: idx={fd.get("index")} orig={fd.get("orig_op")} {fd.get("orig_arg")!r}'
                   f' -> decomp={fd.get("decomp_op")} {fd.get("decomp_arg")!r}')
        try:
            orig = pd._load_code(pyc)
        except Exception as e:
            out.append(f'    !! load pyc failed: {e}')
            continue
        try:
            dec = pd._compile_ok(okp)
        except Exception as e:
            out.append(f'    !! compile OK failed: {type(e).__name__}: {e}')
            continue
        try:
            out.extend(pd.diff_func(orig, dec, m['name'], args.ctx))
        except Exception as e:
            out.append(f'    !! diff failed: {type(e).__name__}: {e}')
        if time.time() - t0 > 240:
            out.append(f'## TIME BUDGET stop at {i}')
            break
    Path(args.out).write_text('\n'.join(out), encoding='utf-8')
    print(f'wrote {args.out} lines={len(out)} elapsed={time.time()-t0:.1f}s')


if __name__ == '__main__':
    main()
