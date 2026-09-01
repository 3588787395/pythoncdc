"""跨进程复现性扫描器。

用法: PYTHONHASHSEED=<seed> D:/Python/python.exe nondet_scan.py <seed> <n>

从 pyc_index.json 取前 n 个 status=='ok' 的 pyc，逐个反编译，
把产物的 md5 写到 results/hash_<seed>.txt，供不同 seed 之间比对。
"""
import sys
import os
import json
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r'F:\Downloads\pythoncdc-main'


def main():
    seed = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    sys.path.insert(0, ROOT)
    from scripts import pyc_batch_verify as pbv

    idx = json.load(open(os.path.join(ROOT, 'pyc_index.json'), encoding='utf-8'))
    targets = [x['path'] for x in idx if x.get('decompile_status') == 'ok'][:n]

    out_dir = os.path.join(HERE, 'results')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'hash_%s.txt' % seed)

    rows = []
    for p in targets:
        try:
            r = pbv.decompile_single(p)
        except Exception as e:
            rows.append('%s\tEXC:%s' % (p, type(e).__name__))
            continue
        if not r.get('success'):
            rows.append('%s\tFAIL' % p)
            continue
        try:
            src = open(r['ok_py_path'], encoding='utf-8', errors='replace').read()
        except Exception as e:
            rows.append('%s\tREADERR:%s' % (p, type(e).__name__))
            continue
        rows.append('%s\t%s' % (p, hashlib.md5(src.encode('utf-8')).hexdigest()))

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(rows) + '\n')
    print('seed=%s files=%d -> %s' % (seed, len(rows), out_path))


if __name__ == '__main__':
    main()
