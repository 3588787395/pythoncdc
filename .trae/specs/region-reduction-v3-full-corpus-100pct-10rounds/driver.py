#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3 规范主代理驱动（归档工具，不进 scripts/）。

判据唯一 = scripts/pyc_verify.py（pylingual equivalence_check）；本文件只做编排，不含任何判定逻辑。
用法：
  python -X utf8 driver.py regen  <shard 0-7 | all> [start] [end]   # 重生成该分片全部 OK.py 产物
  python -X utf8 driver.py verify <shard 0-7 | all34>               # pyc_verify batch → 报告
  python -X utf8 driver.py compare <shard>                          # compare before/after（含单元级差值）
  python -X utf8 driver.py agg   <report_dir_glob>                  # 按相对路径聚合单元读数
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
BL = os.path.join(HERE, 'baseline', 'shards')
SMALL = os.path.join(HERE, 'baseline', 'small34_index.json')
PY = sys.executable

# 本文件在 .trae/specs/<change-id>/ 下，仓库根 = 上溯三级。根算错时每次 regen 都会
# 以 "can't open file .../pycdc.py" 全片失败，故在此钉死，不允许静默跑空。
if not os.path.isfile(os.path.join(ROOT, 'pycdc.py')):
    sys.exit('[fatal] ROOT 解析错误：%s 下没有 pycdc.py' % ROOT)


def shard_json(n):
    return os.path.join(BL, 'shard%d.json' % n)


def load(p):
    with open(p, encoding='utf-8-sig') as f:
        return json.load(f)


def run(args, timeout, label, log):
    t0 = time.time()
    try:
        r = subprocess.run([str(a) for a in args], cwd=ROOT, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=timeout)
        rc, out = r.returncode, (r.stdout or '') + (('\n[stderr] ' + r.stderr) if r.stderr else '')
    except subprocess.TimeoutExpired as e:
        rc, out = 'TIMEOUT', '[TIMEOUT] %s' % str(e)[:300]
    line = '=== %s rc=%s %.1fs' % (label, rc, time.time() - t0)
    with open(log, 'a', encoding='utf-8') as f:
        f.write(line + '\n' + out[-2000:] + '\n')
    print(line, flush=True)
    return rc, out


def cmd_regen(n, start, end, log):
    entries = load(shard_json(n))
    tail = len(entries) if end is None else end
    todo = entries[start:tail]
    failed = []
    for i, e in enumerate(todo, start):
        pyc, ok = e['path'], e['path'][:-4] + 'OK.py'
        try:
            r = subprocess.run([PY, 'pycdc.py', '-o', ok, pyc], cwd=ROOT, capture_output=True,
                               text=True, encoding='utf-8', errors='replace', timeout=90)
            bad = r.returncode != 0 or not os.path.exists(ok)
        except subprocess.TimeoutExpired:
            r, bad = None, True
        if bad:
            failed.append({'path': pyc, 'rc': getattr(r, 'returncode', 'timeout'),
                           'err': ((getattr(r, 'stderr', '') or getattr(r, 'stdout', '') or ''))[-300:]})
            print('[FAIL-REGEN] %s' % pyc.split('site-packages/')[-1], flush=True)
    out = os.path.join(HERE, 'regen_shard%d.json' % n)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(failed, f, ensure_ascii=False, indent=1)
    line = 'regen shard%d [%d:%d]: %d ok, %d failed -> %s' % (
        n, start, tail, len(todo) - len(failed), len(failed), out)
    with open(log, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
    print(line, flush=True)


def cmd_verify(n, log, dest_dir=None):
    if n == 'all34':
        idx, label = SMALL, 'small34'
    else:
        idx, label = shard_json(n), 'shard%d' % n
    dest = dest_dir or BL
    out = os.path.join(dest, label + '_report.json')
    rc, o = run([PY, '-X', 'utf8', 'scripts/pyc_verify.py', 'batch', '--index', idx, '--json', out],
                290, 'verify %s' % label, log)
    return rc, out


def cmd_compare(before, after, label, log):
    return run([PY, '-X', 'utf8', 'scripts/pyc_verify.py', 'compare', '--before', before,
                '--after', after], 120, 'compare %s' % label, log)


def unit_delta(before_report, after_report):
    """文件级 + 单元级双门禁：status 由 success 回落 或 单文件 units_success 下降都算回退。"""
    rows_b = {r['pyc'].split('site-packages/')[-1]: r for r in load(before_report)['rows']}
    rows_a = {r['pyc'].split('site-packages/')[-1]: r for r in load(after_report)['rows']}
    regress, improved, unit_reg = [], [], []
    for k in sorted(set(rows_b) & set(rows_a)):
        b, a = rows_b[k], rows_a[k]
        if b['status'] == 'success' and a['status'] != 'success':
            regress.append(k)
        if b['status'] != 'success' and a['status'] == 'success':
            improved.append(k)
        if a['units_success'] < b['units_success']:
            unit_reg.append('%s %d->%d' % (k, b['units_success'], a['units_success']))
    return {'files_compared': len(set(rows_b) & set(rows_a)),
            'units_before': sum(r['units_success'] for r in rows_b.values()),
            'units_after': sum(r['units_success'] for r in rows_a.values()),
            'file_regressions': regress, 'file_improvements': improved,
            'unit_regressions': unit_reg}


def cmd_agg(pattern, log):
    acc = {}
    for p in glob.glob(pattern):
        for r in load(p)['rows']:
            acc[r['pyc'].split('site-packages/')[-1]] = r
    tot = sum(r['units_total'] for r in acc.values())
    ok = sum(r['units_success'] for r in acc.values())
    buckets = {}
    for r in acc.values():
        buckets[r['status']] = buckets.get(r['status'], 0) + 1
    out = {'files': len(acc), 'units_success': ok, 'units_total': tot,
           'rate': (ok / tot) if tot else None, 'files_by_status': buckets,
           'failing': sorted((r['pyc'].split('site-packages/')[-1], r['units_success'], r['units_total'])
                             for r in acc.values() if r['status'] != 'success')}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    log = os.path.join(HERE, 'driver_log.txt')
    if cmd == 'regen':
        which = sys.argv[2]
        s = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        e = int(sys.argv[4]) if len(sys.argv) > 4 else None
        shards = range(8) if which == 'all' else [int(which)]
        for n in shards:
            cmd_regen(n, s, e, log)
    elif cmd == 'verify':
        which = sys.argv[2]
        dest = sys.argv[3] if len(sys.argv) > 3 else None
        if which == 'all':
            for n in range(8):
                cmd_verify(n, log, dest)
        elif which == 'all34':
            cmd_verify('all34', log, dest)
        else:
            cmd_verify(int(which), log, dest)
    elif cmd == 'compare':
        before = sys.argv[2]
        after = sys.argv[3]
        cmd_compare(before, after, os.path.basename(os.path.dirname(after)), log)
        print(json.dumps(unit_delta(before, after), ensure_ascii=False, indent=1))
    elif cmd == 'agg':
        cmd_agg(sys.argv[2], log)
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
