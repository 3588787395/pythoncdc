#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 3.3 探针读数集合比对：我的 28 探针读数 vs fixP1 / fixP2 / 评审基线。
区分「failure 信息形态变化」与「真实新增失败单元」（按单元名前缀比对）。只读。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    d = json.load(open(os.path.join(HERE, name), encoding='utf-8'))
    rows = d['rows'] if isinstance(d, dict) else d
    return {r['pyc']: r for r in rows}


def fu(x):
    return x.split(': Failure')[0].strip()


def main():
    mine = load('r3v3_probe_results.json')
    print('MINE totals', sum(x['units_success'] for x in mine.values()),
          sum(x['units_total'] for x in mine.values()))
    out = {'mine': {'units_success': sum(x['units_success'] for x in mine.values()),
                    'units_total': sum(x['units_total'] for x in mine.values())}}
    for tag, f in [('fixP1', 'r3v2_probe_results_fixP1.json'),
                   ('fixP2', 'r3v2_probe_results_fixP2.json'),
                   ('review241', 'r3v2_probe_results.json')]:
        b = load(f)
        reg, fixed = [], []
        for p in mine:
            if p in b:
                bf = set(fu(x) for x in b[p]['failures'])
                nf = set(fu(x) for x in mine[p]['failures'])
                if nf - bf:
                    reg.append((p.split('/')[-1], sorted(nf - bf)))
                if bf - nf:
                    fixed.append((p.split('/')[-1], sorted(bf - nf)))
        print(tag, 'base_totals', sum(x['units_success'] for x in b.values()),
              sum(x['units_total'] for x in b.values()),
              'NEWFAIL_units', sum(len(r[1]) for r in reg),
              'FIXED_units', sum(len(r[1]) for r in fixed))
        for r in reg:
            print('   NEWFAIL', r)
        for r in fixed:
            print('   FIXED  ', r)
        out[tag] = {'base_units_success': sum(x['units_success'] for x in b.values()),
                    'newfail_units': sum(len(r[1]) for r in reg),
                    'newfail_detail': reg,
                    'fixed_units': sum(len(r[1]) for r in fixed),
                    'fixed_detail': fixed}
    with open(os.path.join(HERE, 'r3v3_probe_compare.json'), 'w',
              encoding='utf-8', newline='\n') as fp:
        json.dump(out, fp, ensure_ascii=False, indent=1)
    print('-> r3v3_probe_compare.json')


if __name__ == '__main__':
    main()
