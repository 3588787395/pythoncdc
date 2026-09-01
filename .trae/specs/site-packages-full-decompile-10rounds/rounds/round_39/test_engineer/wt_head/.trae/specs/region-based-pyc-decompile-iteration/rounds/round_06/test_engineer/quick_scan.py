"""对指定文件列表做快速验证（秒级），用于定位回归来源。

用法: D:/Python/python.exe quick_scan.py <pyc路径> [更多路径...]
输出每个文件的 status 与函数匹配数（与 full_scan.py 同一判据）。
"""
import os
import sys
import json

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from scripts import pyc_batch_verify as pbv


def scan_one(pyc_path):
    rec = {'path': pyc_path, 'status': 'failed', 'rate': 0.0,
           'total_functions': 0, 'matched_functions': 0, 'error': None}
    try:
        single = pbv.decompile_single(pyc_path)
        if not single['success']:
            rec['error'] = str(single.get('error'))[:120]
            return rec
        diff = pbv.bytecode_diff(pyc_path, single['ok_py_path'])
        if diff.get('error'):
            rec['error'] = str(diff['error'])[:120]
            return rec
        rec['status'] = pbv._classify_decompile_status(
            diff['match_rate'], ok_py_generated=True, py_compile_ok=True)
        rec['rate'] = diff['match_rate']
        rec['total_functions'] = diff['total_functions']
        rec['matched_functions'] = diff['matched_functions']
    except Exception as e:  # noqa: BLE001
        rec['error'] = '%s: %s' % (type(e).__name__, str(e)[:120])
    finally:
        pbv._cleanup_after_pyc()
    return rec


def main():
    paths = sys.argv[1:]
    if not paths:
        print('用法: quick_scan.py <pyc路径> ...')
        return
    for p in paths:
        r = scan_one(p)
        short = p.replace('F:/Downloads/pythoncdc-main/', '')
        print('%-8s %s/%s  %s%s'
              % (r['status'], r['matched_functions'], r['total_functions'],
                 short, ('  ERR:' + r['error']) if r['error'] else ''))


if __name__ == '__main__':
    main()
