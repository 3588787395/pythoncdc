"""统计本轮「容器构造内嵌套三元」判据在全量 402 pyc 上的命中分布。

只做反编译（不做重编译验证），用于量化改动影响面。
打桩 RegionASTGenerator._ternary_nested_in_container_construction 统计命中。

用法: D:/Python/python.exe impact_scan.py [--limit N]
"""
import os
import sys
import json
import time

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg.region_ast_generator import RegionASTGenerator

_orig = RegionASTGenerator._ternary_nested_in_container_construction
_state = {'current': None, 'hits': 0, 'per_file': {}, 'errors': {}}


def patched(self, cond_block):
    try:
        r = _orig(self, cond_block)
    except Exception as e:  # noqa: BLE001
        _state['errors'].setdefault(_state['current'], []).append(
            '%s: %s' % (type(e).__name__, e))
        return False
    if r:
        _state['hits'] += 1
        f = _state['current']
        _state['per_file'][f] = _state['per_file'].get(f, 0) + 1
    return r


RegionASTGenerator._ternary_nested_in_container_construction = patched


def main():
    limit = 0
    if '--limit' in sys.argv:
        limit = int(sys.argv[sys.argv.index('--limit') + 1])

    with open(os.path.join(ROOT, 'pyc_index.json'), 'r', encoding='utf-8') as f:
        entries = json.load(f)
    paths = [e['path'] for e in entries]
    if limit:
        paths = paths[:limit]

    from pycdc import decompile_pyc
    t0 = time.time()
    for i, p in enumerate(paths, 1):
        _state['current'] = p
        try:
            decompile_pyc(p, use_cfg=True)
        except Exception as e:  # noqa: BLE001
            _state['errors'].setdefault(p, []).append(
                'decompile: %s: %s' % (type(e).__name__, str(e)[:80]))
        if i % 100 == 0:
            print('  ... %d/%d (%.0fs) hits=%d'
                  % (i, len(paths), time.time() - t0, _state['hits']), flush=True)

    print()
    print('判据命中总数: %d' % _state['hits'])
    print('命中文件数: %d / %d' % (len(_state['per_file']), len(paths)))
    for p, n in sorted(_state['per_file'].items(), key=lambda x: -x[1]):
        print('  %-3d %s' % (n, p.replace('F:/Downloads/pythoncdc-main/', '')))
    if _state['errors']:
        print('异常文件数: %d' % len(_state['errors']))
        for p, errs in list(_state['errors'].items())[:10]:
            print('  %s: %s' % (p.replace('F:/Downloads/pythoncdc-main/', ''),
                                errs[:2]))


if __name__ == '__main__':
    main()
