#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 位0 补充：v3-tip 对照臂（e10/r8_10/e05 在 v3 tip 两核心文件下的读数）。

判定：v3 tip 红 ⇒ 破口来自 v3 侧 hunk（合并保留）而 v2 独占覆盖在组合中丢失（B104 同类）；
      v3 tip 绿 ⇒ 两方 hunk 交互缝隙。
证据合并入 r9v9fix_b124_4arm.json（arm=v3tip）。核心文件每臂后还原并校验 sha。
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, HERE)
from r9v9fix_b124_4arm import (ANA, GEN, BAKDIR, OUT, PROBES, B124_UNITS,
                               sha, restore_all, probe, load_results)  # noqa: E402

V3 = {'region_analyzer.py': r'D:\Temp\r116\backup\ana_F5_996a1b1acf143458.py',
      'region_ast_generator.py': r'D:\Temp\r116\backup\gen_566ff5c502276e48.py'}


def main():
    os.makedirs(BAKDIR, exist_ok=True)
    for name in ('region_analyzer.py', 'region_ast_generator.py'):
        src = os.path.join(ROOT, 'core', 'cfg', name)
        dst = os.path.join(BAKDIR, name)
        if not os.path.exists(dst):
            with open(src, 'rb') as f, open(dst, 'wb') as g:
                g.write(f.read())
    base_shas = {name: sha(os.path.join(BAKDIR, name))
                 for name in ('region_analyzer.py', 'region_ast_generator.py')}
    for name, src in V3.items():
        with open(src, 'rb') as f:
            data = f.read()
        with open(os.path.join(ROOT, 'core', 'cfg', name), 'wb') as f:
            f.write(data)
        print('v3tip %s sha16=%s' % (name, hashlib.sha256(data).hexdigest()[:16]))
    res = load_results()
    res.setdefault('v3tip_shas', {})
    row = {}
    try:
        for name, rel in PROBES:
            r = probe(rel)
            b124_fail = [u for u in B124_UNITS[name]
                         if any(('.' + u + ':') in fl for fl in r['failures'])]
            row[name] = {'reading': '%s %s/%s' % (r['status'], r['units_success'],
                                                  r['units_total']),
                         'b124_fail': b124_fail, 'failures': r['failures']}
            print('[%-8s %-6s] %-8s %s/%s  B124fail=%s' % (
                'v3tip', name, r['status'], r['units_success'], r['units_total'],
                b124_fail), flush=True)
        res['results']['v3tip'] = row
    finally:
        restore_all()
        for name, s in base_shas.items():
            cur = sha(os.path.join(ROOT, 'core', 'cfg', name))
            assert cur == s, 'RESTORE FAILED %s' % name
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print('-> restored merged bytes OK')


if __name__ == '__main__':
    main()
