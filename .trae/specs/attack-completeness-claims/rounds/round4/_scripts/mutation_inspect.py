#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：变异结果的细查（漏检样例、语料构成、失败原因）。"""
from __future__ import annotations

import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND4 = os.path.abspath(os.path.join(HERE, '..'))
JSONL = os.path.join(ROUND4, '_out', 'mutation_results.jsonl')


def main():
    fam = sys.argv[1] if len(sys.argv) > 1 else None
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    rows = []
    seen = set()
    for line in open(JSONL, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        k = (r['pyc'], r['family'])
        if k in seen:
            continue
        seen.add(k)
        rows.append(r)
    base = {r['pyc']: r for r in rows if r['family'] == 'BASELINE'}
    green = {p for p, r in base.items() if r['status'] == 'success'}
    print('--- corpus by tag ---')
    print(collections.Counter(r['tag'] for r in rows if r['family'] == 'BASELINE'))
    print('baseline total=%d green=%d' % (len(base), len(green)))
    if not fam:
        return
    sel = [r for r in rows if r['family'] == fam and r['pyc'] in green]
    print('\n--- %s : %d rows ---' % (fam, len(sel)))
    print(collections.Counter(r['status'] for r in sel))
    for r in sel:
        if r['status'] == 'success':
            print('MISS  ', r['pyc'])
            print('       site:', r.get('site'))
            print('       mutated:', r.get('mutated'))
            for fl in (r.get('failures') or [])[:1]:
                print('       fail:', fl[:160])
            limit -= 1
            if limit <= 0:
                break
    print('\n--- sample caught failures ---')
    n = 0
    for r in sel:
        if r['status'] == 'failure':
            print('CAUGHT', r['pyc'], '|', (r.get('failures') or [''])[0][:150])
            n += 1
            if n >= 4:
                break


if __name__ == '__main__':
    main()
