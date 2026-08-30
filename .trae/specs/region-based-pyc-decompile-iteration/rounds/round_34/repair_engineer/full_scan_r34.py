"""全量 402 pyc 扫描，输出每文件明细 JSON（用于修复前后严格对比）。

与 scripts/round_batch.py 使用同一套判据（pyc_batch_verify），差别在于
本脚本把每个文件的 status / 函数匹配数写入明细，便于逐文件对比倒退。

用法: D:/Python/python.exe full_scan.py <输出.json> [起始] [数量]
"""
import os
import sys
import json
import time
import argparse

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from scripts import pyc_batch_verify as pbv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--offset', type=int, default=0)
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()

    with open(os.path.join(ROOT, 'pyc_index.json'), 'r', encoding='utf-8') as f:
        entries = json.load(f)

    pending = entries[args.offset:]
    if args.limit:
        pending = pending[:args.limit]

    results = []
    t0 = time.time()
    for idx, entry in enumerate(pending, start=1):
        pyc_path = entry.get('path', '')
        rec = {'path': pyc_path, 'status': 'failed', 'rate': 0.0,
               'total_functions': 0, 'matched_functions': 0, 'error': None}
        if not pyc_path or not os.path.exists(pyc_path):
            rec['error'] = 'pyc file not found'
            results.append(rec)
            continue
        try:
            single = pbv.decompile_single(pyc_path)
            if not single['success']:
                rec['error'] = str(single.get('error'))
                results.append(rec)
                continue
            diff = pbv.bytecode_diff(pyc_path, single['ok_py_path'])
            if diff.get('error'):
                rec['error'] = str(diff['error'])
                results.append(rec)
                continue
            rate = diff['match_rate']
            rec['status'] = pbv._classify_decompile_status(
                rate, ok_py_generated=True, py_compile_ok=True)
            rec['rate'] = rate
            rec['total_functions'] = diff['total_functions']
            rec['matched_functions'] = diff['matched_functions']
        except Exception as e:  # noqa: BLE001
            rec['error'] = '%s: %s' % (type(e).__name__, e)
        results.append(rec)
        pbv._cleanup_after_pyc()
        if idx % 50 == 0:
            print('  ... %d/%d (%.0fs)' % (idx, len(pending), time.time() - t0),
                  flush=True)

    ok = sum(1 for r in results if r['status'] == 'ok')
    pt = sum(1 for r in results if r['status'] == 'partial')
    fl = sum(1 for r in results if r['status'] == 'failed')
    fo = sum(r['matched_functions'] for r in results)
    ft = sum(r['total_functions'] for r in results)
    summary = {'ok': ok, 'partial': pt, 'failed': fl,
               'matched_functions': fo, 'total_functions': ft,
               'elapsed_sec': round(time.time() - t0, 1)}
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump({'summary': summary, 'results': results}, f,
                  ensure_ascii=False, indent=1)
    print('SUMMARY ok=%d partial=%d failed=%d funcs=%d/%d (%.0fs)'
          % (ok, pt, fl, fo, ft, time.time() - t0))


if __name__ == '__main__':
    main()
