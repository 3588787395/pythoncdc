#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分片对半验证并合并 —— 机器争用导致整片超 290s 内部上限时的合规拆跑编排。

判据仍只有 scripts/pyc_verify.py：本文件只做「切半 → 两跑 → 合并 rows」的编排，
不含任何判定逻辑，不改变任何单元的口径。用法：
  python -X utf8 split_verify.py <shard 5|6|7> <dest_dir_abs>
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
if not os.path.isfile(os.path.join(ROOT, 'pycdc.py')):
    sys.exit('[fatal] ROOT 解析错误：%s 下没有 pycdc.py' % ROOT)
PY = sys.executable


def main():
    n = int(sys.argv[1])
    dest = sys.argv[2]
    parts = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    idx = os.path.join(HERE, 'baseline', 'shards', 'shard%d.json' % n)
    entries = json.load(open(idx, encoding='utf-8-sig'))
    step = (len(entries) + parts - 1) // parts
    halves = {}
    for i in range(parts):
        chunk = entries[i * step:(i + 1) * step]
        if not chunk:
            continue
        tag = chr(ord('a') + i)
        p = os.path.join(dest, 'shard%d_%s.json' % (n, tag))
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=1)
        halves[tag] = (p, os.path.join(dest, 'shard%d_%s_report.json' % (n, tag)))
    rows, files_total = [], 0
    for tag, (ip, rp) in halves.items():
        if os.path.isfile(rp):
            os.remove(rp)
        r = subprocess.run([PY, '-X', 'utf8', 'scripts/pyc_verify.py', 'batch',
                            '--index', ip, '--json', rp], cwd=ROOT, capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=280)
        if not os.path.isfile(rp):
            sys.exit('[fatal] shard%d/%s 半片未产出报告 rc=%s：%s'
                     % (n, tag, r.returncode, (r.stderr or r.stdout)[-200:]))
        d = json.load(open(rp, encoding='utf-8'))
        rows += d['rows']
        files_total += d['files_total']
    assert files_total == len(entries) and len(rows) == len(entries), (files_total, len(entries), len(rows))
    units_total = sum(r['units_total'] for r in rows)
    units_ok = sum(r['units_success'] for r in rows)
    cats = ('success', 'failure', 'compile_error', 'error')
    buckets = {c: sorted(r['pyc'] for r in rows if r['status'] == c) for c in cats}
    merged = {'generated_at': json.load(open(halves['a'][1], encoding='utf-8'))['generated_at'],
              'merged_from': [halves[t][1] for t in ('a', 'b')],
              'split_reason': 'contention: full shard exceeded driver 290s internal cap',
              'interpreter': sys.version.split()[0],
              'ruler': json.load(open(halves['a'][1], encoding='utf-8'))['ruler'],
              'files_total': files_total, 'units_total': units_total, 'units_success': units_ok,
              'success_rate': (units_ok / units_total) if units_total else None,
              'files_by_status': {c: len(v) for c, v in buckets.items()},
              'paths_by_status': buckets, 'rows': rows}
    out = os.path.join(dest, 'shard%d_report.json' % n)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(merged, ensure_ascii=False, indent=1, sort_keys=True) + '\n')
    print('shard%d merged: files=%d units=%d/%d buckets=%s'
          % (n, files_total, units_ok, units_total, merged['files_by_status']))


if __name__ == '__main__':
    main()
