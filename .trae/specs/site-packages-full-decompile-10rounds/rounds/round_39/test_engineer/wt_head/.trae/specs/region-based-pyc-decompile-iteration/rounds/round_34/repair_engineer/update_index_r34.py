#!/usr/bin/env python3
"""Round 34 收尾：用 scan_after_fix2_r34.json 结果回写 pyc_index.json。

用法: D:/Python/python.exe update_index_r34.py
将 402 个条目的 decompile_status / bytecode_match_rate / ok_py_generated
更新为扫描结果，last_tested_round 置 34，并备份旧索引。
"""
import json
import os
import shutil
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
IDX = os.path.join(ROOT, 'pyc_index.json')
R34 = os.path.join(ROOT, '.trae', 'specs', 'region-based-pyc-decompile-iteration',
                   'rounds', 'round_34', 'repair_engineer')
SCAN = os.path.join(R34, 'scan_after_fix2_r34.json')


def norm(p):
    return os.path.normcase(os.path.normpath(p.replace('\\', '/')))


def main():
    if not os.path.exists(SCAN):
        print(f'MISSING {SCAN} — 先跑完 3 个分片并合并')
        return 1
    with open(IDX, encoding='utf-8') as f:
        idx = json.load(f)
    with open(SCAN, encoding='utf-8') as f:
        scan = json.load(f)
    scan_map = {norm(r['path']): r for r in scan['results']}
    assert len(scan_map) == 402, f'预期 402 条扫描结果，实际 {len(scan_map)}'

    bak = IDX + '.bak_r34'
    shutil.copyfile(IDX, bak)

    updated = 0
    changed = 0
    for entry in idx:
        r = scan_map.get(norm(entry['path']))
        if r is None:
            continue
        new_status = r['status']
        new_rate = round(r['rate'], 4)
        ok_py = new_status in ('ok', 'partial')
        if (entry.get('decompile_status') != new_status
                or abs(entry.get('bytecode_match_rate', -1) - new_rate) > 1e-9
                or entry.get('ok_py_generated') != ok_py
                or entry.get('matched_functions') != r['matched_functions']
                or entry.get('last_tested_round') != 34):
            changed += 1
        entry['decompile_status'] = new_status
        entry['bytecode_match_rate'] = new_rate
        entry['ok_py_generated'] = ok_py
        entry['matched_functions'] = r['matched_functions']
        entry['last_tested_round'] = 34
        updated += 1

    with open(IDX, 'w', encoding='utf-8') as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)

    from collections import Counter
    print(f'updated {updated}/402, 状态变化 {changed}')
    print('status 分布:', dict(Counter(e['decompile_status'] for e in idx)))
    print(f'备份: {bak}')


if __name__ == '__main__':
    sys.exit(main())
