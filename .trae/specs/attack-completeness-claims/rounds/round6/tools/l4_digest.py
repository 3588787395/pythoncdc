#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 失败样本摘要表（§2 的逐样本行）。

每行给出：来源路径、特征、判据读数、失败单元数、根因类、**一条具体的指令级差异**。
输出：logs/l4_failure_digest.md
"""
from __future__ import annotations

import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND6 = os.path.dirname(HERE)
LOGS = os.path.join(ROUND6, 'logs')
OFF = os.path.join(ROUND6, 'offcorpus')


def main() -> int:
    samples = {s['slug']: s for s in json.load(open(os.path.join(OFF, 'samples.json'),
                                                      encoding='utf-8'))['samples']}
    rows = {}
    for p in sorted(glob.glob(os.path.join(LOGS, 'l4_diff_part*.json'))):
        for r in json.load(open(p, encoding='utf-8'))['rows']:
            rows[r['slug']] = r
    bd = {r['slug']: r for r in json.load(open(os.path.join(LOGS, 'l4_byte_diff.json'),
                                               encoding='utf-8'))['results']}
    cl = {r['slug']: r for r in json.load(open(os.path.join(LOGS, 'l4_classify.json'),
                                              encoding='utf-8'))['rows']}
    sd = {r['slug']: r for r in json.load(open(os.path.join(LOGS, 'l4_source_divergence.json'),
                                              encoding='utf-8'))['results']}
    out = ['# L4 语料外逐样本结果（§2 表数据源）', '',
           '| slug | 来源（真实源码路径） | 特征 | 判据 | 单元(成功/总) | 失败单元 | 根因类 | 具体差异（指令级，摘） |',
           '|---|---|---|---|---|---|---|---|']
    order = sorted(rows)
    for slug in order:
        r = rows[slug]
        v = r.get('verify', {})
        s = samples.get(slug, {})
        cls = cl.get(slug, {})
        units = cl.get(slug, {}).get('units', [])
        diff_head = ''
        if units and units[0].get('diff_head'):
            d = units[0]['diff_head']
            diff_head = ' ／ '.join(x.strip()[:80] for x in d[1:5])
        nfail = len(sd.get(slug, {}).get('units', []))
        out.append('| `%s` | `%s` | %s | %s | %s/%s | %d | %s | %s |' % (
            slug, s.get('src', ''), '、'.join(s.get('features', [])),
            v.get('status'), v.get('units_success'), v.get('units_total'),
            nfail, '、'.join(cls.get('tags', [])), diff_head.replace('|', '/')))
    out.append('')
    out.append('## 逐样本失败单元与差异明细')
    for slug in order:
        r = rows[slug]
        v = r.get('verify', {})
        if v.get('status') != 'failure':
            continue
        out.append('')
        out.append('### `%s`（%s，%s/%s 单元）' % (slug, v.get('status'),
                                                    v.get('units_success'), v.get('units_total')))
        out.append('')
        out.append('- 来源：`%s`' % samples.get(slug, {}).get('src'))
        out.append('- 特征：%s' % '、'.join(samples.get(slug, {}).get('features', [])))
        units = cl.get(slug, {}).get('units', [])
        for u in units:
            out.append('- **`%s`**（根因：%s；指令数 %s→%s）' % (
                u['qualname'], '、'.join(u['tags']), u.get('n_orig_instr'), u.get('n_prod_instr')))
            for line in (u.get('diff_head') or []):
                out.append('  > %s' % line.replace('|', '/'))
    open(os.path.join(LOGS, 'l4_failure_digest.md'), 'w', encoding='utf-8', newline='\n').write(
        '\n'.join(out) + '\n')
    print('-> logs/l4_failure_digest.md (%d samples)' % len(order))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
