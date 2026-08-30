#!/usr/bin/env python3
"""合并 round_33 分块扫描结果并与 round_32 基线逐文件对比（倒退/改进）。

用法: D:/Python/python.exe scan_merge_compare.py
"""
import json
import os
import sys

ROUND = r'F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds'
R33 = os.path.join(ROUND, 'round_33', 'repair_engineer')
R32 = os.path.join(ROUND, 'round_32', 'repair_engineer')


def load(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parts = []
    summaries = []
    for name in ('scan_fix2_part_a.json', 'scan_fix2_part_b.json', 'scan_fix2_part_c.json'):
        p = os.path.join(R33, name)
        if not os.path.exists(p):
            print(f'MISSING: {p}')
            sys.exit(1)
        d = load(p)
        parts.append(d['results'])
        summaries.append(d['summary'])
        print(f'{name}: {d["summary"]["ok"]}ok/{d["summary"]["partial"]}partial '
              f'/{d["summary"]["failed"]}failed '
              f'{d["summary"]["matched_functions"]}/{d["summary"]["total_functions"]} '
              f'({d["summary"]["elapsed_sec"]}s)')

    merged = [r for part in parts for r in part]
    print(f'merged results: {len(merged)}')

    ok = sum(1 for r in merged if r['status'] == 'ok')
    pt = sum(1 for r in merged if r['status'] == 'partial')
    fl = sum(1 for r in merged if r['status'] == 'failed')
    fo = sum(r['matched_functions'] for r in merged)
    ft = sum(r['total_functions'] for r in merged)
    summary = {'ok': ok, 'partial': pt, 'failed': fl,
               'matched_functions': fo, 'total_functions': ft,
               'elapsed_sec': round(sum(s['elapsed_sec'] for s in summaries), 1)}
    out = os.path.join(R33, 'scan_after_fix2.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'summary': summary, 'results': merged}, f,
                  ensure_ascii=False, indent=1)
    print(f'written: {out}')
    print(f'SUMMARY ok={ok} partial={pt} failed={fl} funcs={fo}/{ft}')

    # ── 与 round_32 基线对比 ──
    base = load(os.path.join(R32, 'scan_after_fix.json'))
    base_map = {os.path.normcase(os.path.normpath(r['path'])): r
                for r in base['results']}
    regress = []   # ok→partial/failed 或 partial→failed
    improve = []   # partial→ok / failed→ok 等
    for r in merged:
        key = os.path.normcase(os.path.normpath(r['path']))
        b = base_map.get(key)
        if b is None:
            continue
        bs, ns = b['status'], r['status']
        order = {'ok': 2, 'partial': 1, 'failed': 0}
        if order.get(ns, -1) < order.get(bs, -1):
            regress.append((r['path'], bs, ns, b['rate'], r['rate']))
        elif order.get(ns, -1) > order.get(bs, -1):
            improve.append((r['path'], bs, ns, b['rate'], r['rate']))

    print(f'\n=== 对比 round_32 基线 ===')
    print(f'倒退 {len(regress)}:')
    for p, bs, ns, br, nr in regress:
        print(f'  {os.path.basename(p)}: {bs}({br:.2f}) -> {ns}({nr:.2f})')
    print(f'改进 {len(improve)}:')
    for p, bs, ns, br, nr in improve:
        print(f'  {os.path.basename(p)}: {bs}({br:.2f}) -> {ns}({nr:.2f})')
    if not regress:
        print('>>> 零倒退确认 <<<')
    return 0


if __name__ == '__main__':
    sys.exit(main())
