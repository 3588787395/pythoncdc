"""Round 34 修复: 串行重跑分片中的 failed 文件, 回填到分片 JSON。

用法: D:/Python/python.exe refill_failed_r34.py
遍历 scan_fix2_part_a.json / scan_fix2_part_b.json, 对 status=='failed'
的条目逐一串行重跑 (decompile_single + bytecode_diff), 更新 rate/status
并回写 JSON。用于消除并发资源紧张导致的偶发反编译失败。
"""
import json
import os
import sys
import time

ROOT = r'F:\Downloads\pythoncdc-main'
R34 = os.path.join(ROOT, '.trae', 'specs', 'region-based-pyc-decompile-iteration',
                   'rounds', 'round_34', 'repair_engineer')
sys.path.insert(0, ROOT)

from scripts import pyc_batch_verify as pbv  # noqa: E402

PARTS = ['scan_fix2_part_a.json', 'scan_fix2_part_b.json']


def main():
    for part in PARTS:
        path = os.path.join(R34, part)
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        fixed = 0
        for rec in data['results']:
            if rec['status'] != 'failed':
                continue
            pyc_path = rec['path']
            try:
                single = pbv.decompile_single(pyc_path)
                if not single['success']:
                    print('STILL FAIL %s : %s' % (pyc_path,
                                                  str(single.get('error'))[:80]))
                    continue
                diff = pbv.bytecode_diff(pyc_path, single['ok_py_path'])
                if diff.get('error'):
                    print('STILL FAIL %s : %s' % (pyc_path,
                                                  str(diff['error'])[:80]))
                    continue
                rate = diff['match_rate']
                rec['status'] = pbv._classify_decompile_status(
                    rate, ok_py_generated=True, py_compile_ok=True)
                rec['rate'] = rate
                rec['total_functions'] = diff['total_functions']
                rec['matched_functions'] = diff['matched_functions']
                rec['error'] = None
                fixed += 1
                print('FIXED %-8s %.4f %s' % (rec['status'], rate, pyc_path))
            except Exception as e:  # noqa: BLE001
                rec['error'] = '%s: %s' % (type(e).__name__, e)
                print('EXC %s : %s' % (pyc_path, rec['error'][:80]))
            finally:
                pbv._cleanup_after_pyc()
        # 重算 summary
        ok = sum(1 for r in data['results'] if r['status'] == 'ok')
        pt = sum(1 for r in data['results'] if r['status'] == 'partial')
        fl = sum(1 for r in data['results'] if r['status'] == 'failed')
        fo = sum(r['matched_functions'] for r in data['results'])
        ft = sum(r['total_functions'] for r in data['results'])
        data['summary'] = {
            'ok': ok, 'partial': pt, 'failed': fl,
            'matched_functions': fo, 'total_functions': ft,
            'elapsed_sec': data['summary'].get('elapsed_sec', 0.0),
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('%s: fixed=%d -> summary ok=%d partial=%d failed=%d funcs=%d/%d'
              % (part, fixed, ok, pt, fl, fo, ft))


if __name__ == '__main__':
    main()
