"""Round 35c: 验证两个关键目标文件的字节匹配率。

用法: D:/Python/python.exe verify_r35c_targets.py
目标: quotation.pyc 恢复 143/143；datetime_func.pyc 保持 26/26。
"""
import os
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from scripts import pyc_batch_verify as pbv

TARGETS = [
    r'site-packages\fly\data\quotation.pyc',
    r'site-packages\IQCommon\util\datetime_func.pyc',
]


def main():
    for rel in TARGETS:
        pyc = os.path.join(ROOT, rel)
        print('=== %s ===' % rel)
        try:
            single = pbv.decompile_single(pyc)
            if not single['success']:
                print('  DECOMPILE FAILED: %s' % single.get('error'))
                continue
            ok_py = single['ok_py_path']
            diff = pbv.bytecode_diff(pyc, ok_py)
            if diff.get('error'):
                print('  DIFF ERROR: %s' % diff['error'])
                continue
            rate = diff['match_rate']
            status = pbv._classify_decompile_status(
                rate, ok_py_generated=True, py_compile_ok=True)
            print('  status=%s rate=%.2f funcs=%d/%d' % (
                status, rate,
                diff['matched_functions'], diff['total_functions']))
            if diff.get('unmatched'):
                for u in diff['unmatched'][:8]:
                    print('    UNMATCHED: %s' % u)
            if diff.get('extra'):
                for e in diff['extra'][:8]:
                    print('    EXTRA: %s' % e)
        except Exception as e:  # noqa: BLE001
            print('  EXC: %s: %s' % (type(e).__name__, e))
        finally:
            pbv._cleanup_after_pyc()


if __name__ == '__main__':
    main()
