#!/usr/bin/env python3
"""Round1 shard7 拆分验证（单批 290s 超时 → 两半各自 batch 后合并为 shard7_report_new.json）。
用法: python verify7_split.py   （归档工具，不进 scripts/）
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
BL = os.path.join(ROOT, '.trae', 'specs', 'adversarial-complete-forms-v2-10rounds', 'baseline', 'shards')
CUT = 23


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def run_half(paths, tag):
    out = os.path.join(HERE, '_shard7_%s.json' % tag)
    if os.path.exists(out):
        os.remove(out)
    t0 = time.time()
    r = subprocess.run([sys.executable, 'scripts/pyc_verify.py', 'batch',
                        '--json', out] + paths,
                       cwd=ROOT, capture_output=True, text=True, timeout=290,
                       encoding='utf-8', errors='replace')
    print(r.stdout[-600:])
    if r.returncode != 0:
        print('[%s RC=%d] %s' % (tag, r.returncode, r.stderr[-500:]))
        sys.exit(r.returncode)
    d = load(out)
    print('half %s: %s units=%s/%s elapsed=%.1fs' % (tag, d['files_by_status'],
                                                     d['units_success'], d['units_total'],
                                                     time.time() - t0))
    return d


def merge(a, b):
    m = dict(a)
    m['rows'] = a['rows'] + b['rows']
    m['files_total'] = a['files_total'] + b['files_total']
    m['units_total'] = a['units_total'] + b['units_total']
    m['units_success'] = a['units_success'] + b['units_success']
    m['success_rate'] = m['units_success'] / m['units_total'] if m['units_total'] else 0.0
    fbs = {}
    for d in (a, b):
        for k, v in d['files_by_status'].items():
            fbs[k] = fbs.get(k, 0) + v
    m['files_by_status'] = fbs
    pbs = {}
    for d in (a, b):
        for k, v in d.get('paths_by_status', {}).items():
            pbs.setdefault(k, []).extend(v)
    m['paths_by_status'] = pbs
    m['elapsed_sec'] = a.get('elapsed_sec', 0) + b.get('elapsed_sec', 0)
    return m


if __name__ == '__main__':
    with open(os.path.join(BL, 'shard7.json'), encoding='utf-8-sig') as f:
        paths = [e['path'] for e in json.load(f)]
    regen_fail = {e['path'] for e in load(os.path.join(HERE, 'regen_shard7.json'))}
    paths = [p for p in paths if p not in regen_fail]
    halves = [paths[:CUT], paths[CUT:]]
    reps = [run_half(h, 'a') for h in halves]
    m = merge(*reps)
    out = os.path.join(HERE, 'shard7_report_new.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    print('shard7 MERGED: %s units=%s/%s -> %s' % (m['files_by_status'],
                                                   m['units_success'], m['units_total'], out))
