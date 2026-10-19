#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R3 证据抽取：把指定 stamp JSON 的探针条目按 name 汇总 dump（ok_text / verify_out / failures）。
用法: python _r3_dump.py --json a.json b.json ... --out dir  [--name substr]
"""
import argparse
import json
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', nargs='+', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--names', nargs='*', default=None)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    seen = set()
    idx = {}
    for jf in a.json:
        rows = json.load(open(jf, encoding='utf-8'))
        for r in rows:
            name = r.get('name')
            if a.names and name not in a.names:
                continue
            if name in seen:
                continue
            seen.add(name)
            idx[name] = {'json': os.path.basename(jf), 'status': r.get('status'),
                         'units': '%s/%s' % (r.get('units_success'), r.get('units_total')),
                         'failures': r.get('failures'), 'pyc_src_rel': r.get('pyc_src_rel'),
                         'staged_pyc': r.get('staged_pyc')}
            txt = r.get('ok_text') or ''
            with open(os.path.join(a.out, '%s__regen.py' % name), 'w', encoding='utf-8', newline='\n') as f:
                f.write(txt)
            with open(os.path.join(a.out, '%s__verify.txt' % name), 'w', encoding='utf-8', newline='\n') as f:
                f.write(r.get('verify_out') or '')
    with open(os.path.join(a.out, '_index.json'), 'w', encoding='utf-8') as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)
    for k in sorted(idx):
        print(k, idx[k]['status'], idx[k]['units'], '|', '; '.join(idx[k]['failures'] or []))


if __name__ == '__main__':
    main()
