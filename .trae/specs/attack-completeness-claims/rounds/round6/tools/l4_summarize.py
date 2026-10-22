#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 语料外差分读数汇总（§2 表）。

读入 l4_diff_part*.json，产出：
  * 汇总 JSON（logs/l4_offcorpus_summary.json）
  * Markdown 表（logs/l4_offcorpus_table.md）
  * CSV（logs/offcorpus_diff.csv）
"""
from __future__ import annotations

import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND6 = os.path.dirname(HERE)
LOGS = os.path.join(ROUND6, 'logs')


def main() -> int:
    rows = []
    for p in sorted(glob.glob(os.path.join(LOGS, 'l4_diff_part*.json'))):
        d = json.load(open(p, encoding='utf-8'))
        rows.extend(d['rows'])
    seen = {}
    for r in rows:
        seen[r['slug']] = r
    rows = [seen[k] for k in sorted(seen)]
    for r in rows:
        v = r.get('verify', {})
        r['status'] = v.get('status')
        r['units_success'] = v.get('units_success')
        r['units_total'] = v.get('units_total')
        r['n_fail_units'] = max(0, (r['units_total'] or 0) - (r['units_success'] or 0))
    json.dump({'rows': rows}, open(os.path.join(LOGS, 'l4_offcorpus_summary.json'), 'w',
                                   encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    # CSV
    import csv
    with open(os.path.join(LOGS, 'offcorpus_diff.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['slug', 'origin', 'source_py', 'pyc', 'status', 'units_success',
                    'units_total', 'n_fail_units', 'src_matches_pyc', 'pycdc_elapsed',
                    'verify_elapsed', 'features'])
        for r in rows:
            w.writerow([r['slug'], r.get('origin'), r.get('src'), r.get('pyc_src'),
                        r['status'], r['units_success'], r['units_total'], r['n_fail_units'],
                        r.get('src_matches_pyc'), r['pycdc']['elapsed'],
                        r.get('verify', {}).get('elapsed'), '|'.join(r.get('features', []))])
    # Markdown
    lines = ['| slug | 来源（真实源码路径） | 判据状态 | 单元 | 失败单元 | 源码≡pyc | 特征 |',
             '|---|---|---|---|---|---|---|']
    for r in rows:
        lines.append('| `%s` | `%s` | %s | %s/%s | %s | %s | %s |' % (
            r['slug'], r.get('src'), r['status'], r['units_success'], r['units_total'],
            r['n_fail_units'], r.get('src_matches_pyc'), '、'.join(r.get('features', []))))
    open(os.path.join(LOGS, 'l4_offcorpus_table.md'), 'w', encoding='utf-8', newline='\n').write(
        '\n'.join(lines) + '\n')
    n_ok = sum(1 for r in rows if r['status'] == 'success')
    n_ce = sum(1 for r in rows if r['status'] == 'compile_error')
    n_f = sum(1 for r in rows if r['status'] == 'failure')
    tot_u = sum(r['units_total'] or 0 for r in rows)
    ok_u = sum(r['units_success'] or 0 for r in rows)
    print('samples=%d success=%d failure=%d compile_error=%d | units=%d/%d' % (
        len(rows), n_ok, n_f, n_ce, ok_u, tot_u))
    mism = [r['slug'] for r in rows if r.get('src_matches_pyc') is False]
    print('src!=pyc:', mism)
    return 0


if __name__ == '__main__':
    sys.exit(main()) if False else main()
