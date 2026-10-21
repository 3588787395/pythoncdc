#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L3 执行级语义差分**全量扫描**：探针 × 单元，交叉比对「判定器判定」与「执行级语义」。

目的：检验「判定器判绿 ⇒ 语义等价」这条推断链（baseline/judge_criteria.md §3 B-01）。
输出两列：
  judge_fail   —— `scripts/pyc_verify.py single` 的单元级失败标记（来自探针 .judge.txt）
  semdiff      —— 本轮执行级差分结论（EQUAL / DIFFERENT / TIMEOUT）
出现 `judge_fail=False 且 semdiff=DIFFERENT` 即 **L2 判据盲区实例**。

用法：
    python -X utf8 l3_semdiff_sweep.py [--probes <dir>] [--out <json>]
"""
import argparse
import ast
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
PROBES = os.path.abspath(os.path.join(HERE, '..', 'probes'))
SEMDIFF = os.path.abspath(os.path.join(HERE, 'l3_semdiff.py'))


def probe_funcs(path):
    tree = ast.parse(open(path, encoding='utf-8').read())
    return [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def judge_fails(probe):
    """从探针旁的 .judge.txt 解析失败单元名。"""
    jp = os.path.join(PROBES, probe + '.judge.txt')
    fails = set()
    if os.path.isfile(jp):
        for line in open(jp, encoding='utf-8', errors='replace'):
            s = line.strip()
            if s.startswith('***'):
                unit = s.split(':', 1)[0].replace('***', '').strip()
                fails.add(unit.split('.')[-1] if unit else '')
    return fails


def run_semdiff(probe, func, timeout=300):
    """返回 (聚合判定, 逐用例明细 JSON)：任一用例 DIFFERENT ⇒ 聚合为 DIFFERENT。"""
    cmd = [sys.executable, '-X', 'utf8', SEMDIFF, probe, func]
    try:
        p = subprocess.run(cmd, capture_output=True, encoding='utf-8',
                           errors='replace', timeout=timeout)
    except subprocess.TimeoutExpired:
        return 'TIMEOUT', ''
    cases = []
    for line in (p.stdout or '').splitlines():
        s = line.strip()
        if not s or s.startswith('->'):
            continue
        try:
            cases.append(json.loads(s))
        except ValueError:
            return 'ERROR', s[:200]
    if not cases:
        return 'ERROR', (p.stderr or '')[-200:]
    diffs = [c for c in cases if c.get('verdict') == 'DIFFERENT']
    if diffs:
        verdict = 'DIFFERENT'
    elif any(c.get('verdict') == 'TIMEOUT' for c in cases):
        verdict = 'TIMEOUT'
    else:
        verdict = 'EQUAL'
    detail = json.dumps({'cases': len(cases),
                         'differing': [c.get('source', {}) for c in diffs]},
                        ensure_ascii=False, default=str)[:1500]
    return verdict, detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--probes', default=PROBES)
    ap.add_argument('--out', default=os.path.join(HERE, '..', 'logs', 'l3_semdiff_sweep.json'))
    a = ap.parse_args()
    probes = sorted(n[:-3] for n in os.listdir(a.probes)
                    if n.endswith('.py') and not n.endswith('OK.py'))
    rows = []
    for pr in probes:
        fails = judge_fails(pr)
        for fn in probe_funcs(os.path.join(a.probes, pr + '.py')):
            verdict, detail = run_semdiff(pr, fn)
            jf = fn in fails
            rows.append({'probe': pr, 'func': fn, 'judge_fail': jf,
                         'semdiff': verdict, 'detail': detail})
            print('%-42s %-30s judge_fail=%-5s semdiff=%s' % (pr, fn, jf, verdict),
                  flush=True)
    blind = [r for r in rows if not r['judge_fail'] and r['semdiff'] in ('DIFFERENT', 'TIMEOUT')]
    print('\n-> units=%d judge_fail=%d semdiff_DIFFERENT=%d' % (
        len(rows), sum(1 for r in rows if r['judge_fail']),
        sum(1 for r in rows if r['semdiff'] in ('DIFFERENT', 'TIMEOUT'))))
    print('-> L2 blind-spot candidates (judge green but execution differs) = %d' % len(blind))
    for r in blind:
        print('   %s :: %s  (%s)' % (r['probe'], r['func'], r['semdiff']))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(os.path.abspath(a.out), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'rows': rows, 'blind_spot_candidates': blind}, f,
                  ensure_ascii=False, indent=1, default=str)
    return 0


if __name__ == '__main__':
    sys.exit(main())
