"""把 9 个不可复现文件在某 seed 下的产物快照保存到 variants/<seed>/。

用法: PYTHONHASHSEED=<seed> D:/Python/python.exe dump_variants.py <seed>
"""
import sys
import os
import json
import shutil

ROOT = r'F:\Downloads\pythoncdc-main'
HERE = os.path.dirname(os.path.abspath(__file__))

TARGETS = [
    'site-packages/IQCommon/arg_checker.pyc',
    'site-packages/IQCommon/const.pyc',
    'site-packages/IQCommon/logger/__init__.pyc',
    'site-packages/IQData/utils/arg_checker.pyc',
    'site-packages/IQData/utils/logger/logger.pyc',
    'site-packages/IQEngine/const.pyc',
    'site-packages/IQEngine/plugins/plugin_system_trade/enums.pyc',
    'site-packages/IQEngine/utils/arg_checker.pyc',
    'site-packages/fly/data/quotation.pyc',
]


def main():
    seed = sys.argv[1]
    sys.path.insert(0, ROOT)
    from scripts import pyc_batch_verify as pbv

    out_dir = os.path.join(HERE, 'variants', 'seed_%s' % seed)
    os.makedirs(out_dir, exist_ok=True)

    for rel in TARGETS:
        p = os.path.join(ROOT, rel).replace('\\', '/')
        try:
            r = pbv.decompile_single(p)
        except Exception as e:
            print('EXC', rel, type(e).__name__)
            continue
        if not r.get('success'):
            print('FAIL', rel)
            continue
        dst = os.path.join(out_dir, rel.replace('/', '__').replace('.pyc', '.py'))
        shutil.copyfile(r['ok_py_path'], dst)
        print('ok', rel)


if __name__ == '__main__':
    main()
