#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：漏检样本取证（逐条打印产物↔变异的文本差异 + 判据读数）。

用法：
  python -X utf8 miss_inspect.py <family> [max_rows]
"""
from __future__ import annotations

import difflib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND4 = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(ROUND4, '..', '..', '..', '..', '..'))
JSONL = os.path.join(ROUND4, '_out', 'mutation_results.jsonl')


def load():
    rows = []
    seen = set()
    for line in open(JSONL, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        key = (r['pyc'], r['family'])
        if key in seen:
            continue
        seen.add(key)
        rows.append(r)
    return rows


def main():
    fam = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    rows = load()
    base = {r['pyc']: r for r in rows if r['family'] == 'BASELINE'}
    green = {p for p, r in base.items() if r['status'] == 'success'}
    hits = [r for r in rows
            if r['family'] == fam and r['status'] == 'success' and r['pyc'] in green]
    print('MISS rows for %s: %d' % (fam, len(hits)))
    for r in hits[:limit]:
        prod = r['pyc'][:-4] + 'OK.py'
        mut = os.path.join(ROOT, r['mutated'].replace('/', os.sep))
        print('=' * 100)
        print('pyc    :', r['pyc'])
        print('product:', prod)
        print('mutated:', mut)
        print('site   :', r.get('site'))
        print('units  :', r.get('units'), ' failures:', r.get('failures'))
        a = open(prod, encoding='utf-8', errors='replace').read().splitlines()
        b = open(mut, encoding='utf-8', errors='replace').read().splitlines()
        for line in difflib.unified_diff(a, b, 'product', 'mutated', lineterm='', n=1):
            print('   ', line)


if __name__ == '__main__':
    main()
