"""统计「同名 code object 覆盖」造成的度量盲点。

scripts/pyc_batch_verify._extract_code_objects 以 co_name 为键建映射，同名者
后者覆盖前者，因此重名函数中只有最后一个会被真正比对。本脚本统计每个 pyc 的
code object 总数、唯一名数、被遮蔽数。

用法: D:/Python/python.exe dupname_scan.py [输出.json]
"""
import sys
import os
import json
import types
import collections

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)


def walk(co, out):
    out.append(co)
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)


def load_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        data = f.read()
    return marshal.loads(data[16:])


import marshal  # noqa: E402


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else None
    with open(os.path.join(ROOT, 'pyc_index.json'), encoding='utf-8') as f:
        entries = json.load(f)
    total_codes = 0
    total_unique = 0
    files_with_dup = 0
    worst = []
    per_file = []
    for e in entries:
        p = e['path']
        try:
            co = load_code(p)
        except Exception:
            continue
        codes = []
        walk(co, codes)
        names = collections.Counter(c.co_name or '<module>' for c in codes)
        dups = {n: k for n, k in names.items() if k > 1}
        shadowed = sum(k - 1 for k in dups.values())
        total_codes += len(codes)
        total_unique += len(names)
        if dups:
            files_with_dup += 1
            worst.append((shadowed, os.path.basename(p), dups))
        per_file.append({'path': p, 'codes': len(codes),
                         'unique': len(names), 'shadowed': shadowed,
                         'dups': dups})
    worst.sort(key=lambda x: -x[0])
    print('pyc 文件数            : %d' % len(per_file))
    print('code object 总数      : %d' % total_codes)
    print('唯一名数（实际比对数）: %d' % total_unique)
    print('被遮蔽（未比对）      : %d  (%.2f%%)'
          % (total_codes - total_unique,
             100.0 * (total_codes - total_unique) / max(total_codes, 1)))
    print('含重名的文件数        : %d / %d'
          % (files_with_dup, len(per_file)))
    print('--- 遮蔽最多的前 10 个文件 ---')
    for shadowed, base, dups in worst[:10]:
        print('  %-42s shadowed=%-3d %s'
              % (base, shadowed,
                 ', '.join('%s×%d' % (n, k)
                           for n, k in sorted(dups.items(),
                                              key=lambda x: -x[1])[:6])))
    if out_path:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump({'summary': {
                          'files': len(per_file),
                          'codes': total_codes,
                          'unique': total_unique,
                          'shadowed': total_codes - total_unique,
                          'files_with_dup': files_with_dup},
                       'per_file': per_file}, f, ensure_ascii=False, indent=1)
        print('written ->', out_path)


if __name__ == '__main__':
    main()
