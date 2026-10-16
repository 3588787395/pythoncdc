#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 位0 补充：v2-tip（91f8d27d）两核心文件臂 + 交叉臂（ana/gen 分文件归因）。

臂：
  v2tip      = 两文件均取 v2 tip（git show 91f8d27d:core/cfg/<f>）
  v2a_mg     = v2 tip analyzer + merged generator
  mg_v2a...  = merged analyzer + v2 tip generator（= v2g_ma）
判定哪个文件承载 e10/r8_10 的丢失。证据合并入 r9v9fix_b124_4arm.json。
"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, HERE)
from r9v9fix_b124_4arm import (BAKDIR, OUT, PROBES, B124_UNITS,
                               sha, restore_all, probe, load_results)  # noqa: E402

V2_COMMIT = '91f8d27d'


def git_bytes(rel):
    p = subprocess.run(['git', 'show', '%s:%s' % (V2_COMMIT, rel)],
                       capture_output=True, cwd=ROOT)
    assert p.returncode == 0 and p.stdout, 'git show failed for %s' % rel
    return p.stdout


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
    arm = sys.argv[1]
    assert arm in ('v2tip', 'v2a_mg', 'ma_v2g'), arm
    files = {
        'v2tip': {'region_analyzer.py': 'v2', 'region_ast_generator.py': 'v2'},
        'v2a_mg': {'region_analyzer.py': 'v2', 'region_ast_generator.py': 'merged'},
        'ma_v2g': {'region_analyzer.py': 'merged', 'region_ast_generator.py': 'v2'},
    }[arm]
    for name, which in files.items():
        if which == 'v2':
            data = git_bytes('core/cfg/' + name)
        else:
            with open(os.path.join(BAKDIR, name), 'rb') as f:
                data = f.read()
        with open(os.path.join(ROOT, 'core', 'cfg', name), 'wb') as f:
            f.write(data)
        print('%s %s=%s sha16=%s' % (arm, name, which,
                                     hashlib.sha256(data).hexdigest()[:16]))
    res = load_results()
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
                arm, name, r['status'], r['units_success'], r['units_total'],
                b124_fail), flush=True)
        res['results'][arm] = row
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
