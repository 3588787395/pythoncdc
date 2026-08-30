"""列出指定 pyc 中不匹配的函数名（叶子级），用于修复前后精确对比。

用法: D:/Python/python.exe list_mismatch.py <pyc路径> [更多路径...]
"""
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from scripts import pyc_batch_verify as pbv


def main():
    for pyc in sys.argv[1:]:
        try:
            single = pbv.decompile_single(pyc)
            if not single['success']:
                print('%s  DECOMPILE-FAILED %s' % (pyc, single.get('error')))
                continue
            diff = pbv.bytecode_diff(pyc, single['ok_py_path'])
            if diff.get('error'):
                print('%s  DIFF-ERROR %s' % (pyc, diff['error']))
                continue
            print('%s  %d/%d matched  rate=%.4f'
                  % (pyc, diff['matched_functions'], diff['total_functions'],
                     diff['match_rate']))
            for f in (diff.get('mismatches') or []):
                fd = f.get('first_diff') or {}
                print('    MISMATCH %-26s orig=%s decomp=%s  first=%s vs %s'
                      % (f.get('name'), f.get('orig_count'),
                         f.get('decomp_count'),
                         fd.get('orig'), fd.get('decomp')))
            for n in (diff.get('missing_in_decomp') or []):
                print('    MISSING  %s' % n)
            for n in (diff.get('extra_in_decomp') or []):
                print('    EXTRA    %s' % n)
        except Exception as e:  # noqa: BLE001
            print('%s  EXC %s: %s' % (pyc, type(e).__name__, e))
        finally:
            pbv._cleanup_after_pyc()


if __name__ == '__main__':
    main()
