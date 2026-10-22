#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 合并 §4 的边界读数分片（l4_bnd_*.json / l4_boundary_a.json）为单文件。

输出：logs/l4_boundary.json（按名称去重，保留最后一次读数）
"""
from __future__ import annotations

import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND6 = os.path.dirname(HERE)
LOGS = os.path.join(ROUND6, 'logs')


def main() -> int:
    rows = {}
    for p in sorted(glob.glob(os.path.join(LOGS, 'l4_bnd_*.json')) + \
                    glob.glob(os.path.join(LOGS, 'l4_boundary_a.json'))):
        for r in json.load(open(p, encoding='utf-8'))['rows']:
            rows[r['name']] = r
    out = [rows[k] for k in sorted(rows)]
    with open(os.path.join(LOGS, 'l4_boundary.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'rows': out}, f, ensure_ascii=False, indent=1)
    print('-> logs/l4_boundary.json (%d cases)' % len(out))
    for r in out:
        print('  %-18s %-26s pycdc=%ss verify=%s verdict=%s' % (
            r['name'], r.get('desc', ''),
            r.get('pycdc', {}).get('elapsed'), r.get('verify', {}).get('status'), r.get('verdict')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
