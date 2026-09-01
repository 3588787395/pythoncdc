"""用全量扫描结果同步 pyc_index.json。

用法: sync_index.py <scan.json> <round>
只写回真正变化的字段，保证 diff 行数 == 变化条目数（不整文件重写）。
"""
import io
import json
import os
import sys

ROOT = 'F:/Downloads/pythoncdc-main'
INDEX = os.path.join(ROOT, 'pyc_index.json')


def norm(p):
    return p.replace('\\', '/')


def main():
    scan_path, rnd = sys.argv[1], int(sys.argv[2])
    with io.open(scan_path, encoding='utf-8') as f:
        scan = json.load(f)
    results = scan['results'] if isinstance(scan, dict) else scan
    smap = {norm(r['path']): r for r in results}

    with io.open(INDEX, encoding='utf-8', newline='') as f:
        raw = f.read()
    idx = json.loads(raw)
    endswith_nl = raw.endswith('\n')

    changed = 0
    for it in idx:
        s = smap.get(norm(it['path']))
        if s is None:
            continue
        touched = False
        if it.get('decompile_status') != s['status']:
            it['decompile_status'] = s['status']
            touched = True
        if abs(it.get('bytecode_match_rate', -1) - s['rate']) > 1e-9:
            it['bytecode_match_rate'] = s['rate']
            touched = True
        # partial 专属字段：仅在仍为 partial 时保留
        if s['status'] == 'partial':
            for k, v in (('matched_functions', s['matched_functions']),
                         ('total_functions', s['total_functions']),
                         ('mismatch_count', s['total_functions'] - s['matched_functions']),
                         ('match_rate', round(s['rate'], 4))):
                if it.get(k) != v:
                    it[k] = v
                    touched = True
        else:
            for k in ('matched_functions', 'total_functions', 'mismatch_count', 'match_rate'):
                if k in it:
                    del it[k]
                    touched = True
        if it.get('last_tested_round') != rnd:
            it['last_tested_round'] = rnd
            touched = True
        if touched:
            changed += 1

    out = json.dumps(idx, ensure_ascii=False, indent=2)
    if endswith_nl:
        out += '\n'
    with io.open(INDEX, 'w', encoding='utf-8', newline='') as f:
        f.write(out)
    print('changed entries:', changed)


if __name__ == '__main__':
    main()
