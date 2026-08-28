#!/usr/bin/env python3
"""分块批量验证工具（轮次迭代用）。

与 scripts/pyc_batch_verify.py 的 batch 子命令功能一致，但额外支持：
  --offset  N   跳过前 N 个待验证条目（用于把长批次切分为多个 <300s 的命令）
  --budget  S   秒级时间预算，超时后停止并保留已完成结果
  --out     P   把每个文件的详细结果写入 JSON（供测试工程师做问题分类）
  --targets F   只验证 F 中列出的文件（每行一个路径），忽略索引状态

用法：
  D:/Python/python.exe scripts/round_batch.py --round 2 --offset 0 --budget 280 \
      --out .trae/specs/<spec>/rounds/round_02/baseline/batch_000.json
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import pyc_batch_verify as pbv  # noqa: E402

DEFAULT_INDEX = str(PROJECT_ROOT / 'pyc_index.json')


def _safe(v):
    """把 first_diff 等内部结构转成 JSON 可序列化的形式。"""
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, (list, tuple)):
        return [_safe(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _safe(x) for k, x in v.items()}
    return repr(v)


def _as_count(v):
    """diff 项里的 jump_diffs/true_diffs 可能是列表或计数，统一成整数。"""
    if v is None:
        return 0
    if isinstance(v, int):
        return v
    try:
        return len(v)
    except TypeError:
        return 0


def main():
    ap = argparse.ArgumentParser(description='分块批量 pyc 验证')
    ap.add_argument('--index', default=DEFAULT_INDEX)
    ap.add_argument('--round', type=int, default=0)
    ap.add_argument('--offset', type=int, default=0)
    ap.add_argument('--budget', type=float, default=280.0)
    ap.add_argument('--out', default=None)
    ap.add_argument('--targets', default=None,
                    help='只验证该文件中的路径列表（每行一个）')
    ap.add_argument('--no-write-index', action='store_true')
    args = ap.parse_args()

    index_file = Path(args.index)
    with open(index_file, 'r', encoding='utf-8') as f:
        entries = json.load(f)

    if args.targets:
        with open(args.targets, 'r', encoding='utf-8') as f:
            want = [os.path.normcase(os.path.normpath(l.strip()))
                    for l in f if l.strip()]
        want_set = set(want)
        pending = [e for e in entries
                   if os.path.normcase(os.path.normpath(e.get('path', ''))) in want_set]
    else:
        pending = [e for e in entries if e.get('decompile_status') != 'ok']

    pending = pending[args.offset:]
    print(f'[ROUND_BATCH] index={index_file} round={args.round} '
          f'pending={len(pending)} offset={args.offset} budget={args.budget:.0f}s')

    results = []
    t0 = time.time()
    done = 0
    for idx, entry in enumerate(pending, start=1):
        elapsed = time.time() - t0
        if elapsed > args.budget:
            print(f'[ROUND_BATCH] budget reached after {done} files '
                  f'({elapsed:.0f}s), stopping.')
            break
        pyc_path = entry.get('path', '')
        rec = {'path': pyc_path, 'status': None, 'rate': 0.0,
               'total_functions': 0, 'matched_functions': 0,
               'mismatches': [], 'error': None}
        if not pyc_path or not os.path.exists(pyc_path):
            rec['status'] = 'failed'
            rec['error'] = 'pyc file not found'
            results.append(rec)
            continue
        try:
            single = pbv.decompile_single(pyc_path)
        except Exception as e:  # noqa: BLE001
            rec['status'] = 'failed'
            rec['error'] = f'decompile_exception: {type(e).__name__}: {e}'
            results.append(rec)
            done += 1
            continue
        if not single['success']:
            rec['status'] = 'failed'
            rec['error'] = single['error']
            results.append(rec)
            done += 1
            continue
        try:
            diff = pbv.bytecode_diff(pyc_path, single['ok_py_path'])
        except Exception as e:  # noqa: BLE001
            rec['status'] = 'failed'
            rec['error'] = f'diff_exception: {type(e).__name__}: {e}'
            results.append(rec)
            done += 1
            continue
        if diff.get('error'):
            rec['status'] = 'failed'
            rec['error'] = diff['error']
            results.append(rec)
            done += 1
            continue
        rate = diff['match_rate']
        rec['status'] = pbv._classify_decompile_status(
            rate, ok_py_generated=True, py_compile_ok=True)
        rec['rate'] = rate
        rec['total_functions'] = diff['total_functions']
        rec['matched_functions'] = diff['matched_functions']
        rec['missing_in_decomp'] = diff.get('missing_in_decomp', [])
        rec['extra_in_decomp'] = diff.get('extra_in_decomp', [])
        rec['mismatches'] = [
            {'name': m['name'],
             'orig_count': m.get('orig_count'),
             'decomp_count': m.get('decomp_count'),
            'jump_diffs': _as_count(m.get('jump_diffs')),
            'true_diffs': _as_count(m.get('true_diffs')),
             'first_diff': _safe(m.get('first_diff'))}
            for m in diff.get('mismatches', [])
        ]
        entry['bytecode_match_rate'] = rate
        entry['decompile_status'] = rec['status']
        entry['ok_py_generated'] = True
        entry['last_tested_round'] = args.round
        entry.pop('error', None)
        print(f'  [{idx}] {rec["status"].upper():8s} '
              f'{rec["matched_functions"]}/{rec["total_functions"]} '
              f'{os.path.basename(pyc_path)}')
        results.append(rec)
        done += 1
        pbv._cleanup_after_pyc()

    if not args.no_write_index:
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

    summary = {
        'round': args.round,
        'offset': args.offset,
        'elapsed_sec': round(time.time() - t0, 1),
        'processed': done,
        'remaining': len(pending) - done,
        'ok': sum(1 for r in results if r['status'] == 'ok'),
        'partial': sum(1 for r in results if r['status'] == 'partial'),
        'failed': sum(1 for r in results if r['status'] == 'failed'),
        'total_functions': sum(r['total_functions'] for r in results),
        'matched_functions': sum(r['matched_functions'] for r in results),
        'files': results,
    }
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                       encoding='utf-8')
        print(f'[ROUND_BATCH] detail written: {out}')
    print('[ROUND_BATCH] SUMMARY ok=%d partial=%d failed=%d funcs=%d/%d' % (
        summary['ok'], summary['partial'], summary['failed'],
        summary['matched_functions'], summary['total_functions']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
