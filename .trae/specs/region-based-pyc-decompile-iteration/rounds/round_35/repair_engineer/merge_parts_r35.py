"""Round 35c: 合并 3 个分片扫描结果并重新汇总。

用法: D:/Python/python.exe merge_parts_r35.py
输入: scan_fix3_part_{a,b,c}.json
输出: scan_after_fix_r35.json（供 update_index_r35.py / merge_and_compare_r35.py 使用）
"""
import json
import os

ROOT = r'F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_35\repair_engineer'
PARTS = ['scan_fix3_part_a.json', 'scan_fix3_part_b.json', 'scan_fix3_part_c.json']
OUT = os.path.join(ROOT, 'scan_after_fix_r35.json')


def main():
    results = []
    for p in PARTS:
        path = os.path.join(ROOT, p)
        if not os.path.exists(path):
            print('MISSING %s' % path)
            return 1
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        results.extend(data['results'])
        print('%s: %d 条, summary=%s' % (p, len(data['results']), data['summary']))

    seen = {}
    for r in results:
        seen[os.path.normcase(os.path.normpath(r['path'].replace('\\', '/')))] = r
    if len(seen) != 402:
        print('WARN: 去重后 %d 条（预期 402）' % len(seen))
        return 1

    ok = sum(1 for r in results if r['status'] == 'ok')
    pt = sum(1 for r in results if r['status'] == 'partial')
    fl = sum(1 for r in results if r['status'] == 'failed')
    fo = sum(r['matched_functions'] for r in results)
    ft = sum(r['total_functions'] for r in results)
    summary = {'ok': ok, 'partial': pt, 'failed': fl,
               'matched_functions': fo, 'total_functions': ft}
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump({'summary': summary, 'results': results}, f,
                  ensure_ascii=False, indent=1)
    print('MERGED -> %s' % OUT)
    print('SUMMARY ok=%d partial=%d failed=%d funcs=%d/%d' % (
        ok, pt, fl, fo, ft))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
