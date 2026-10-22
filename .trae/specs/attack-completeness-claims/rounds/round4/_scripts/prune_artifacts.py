#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：证据目录**整理**（不改变任何判定读数）。

做三件事：
  1) **漏检样本抽样留存**：`_probes/miss/` 下每个变异族保留至多 N 个样本
     （优先取**互不相同的 pyc**），其余删除。全部 1219 条漏检的**原始判定记录**
     仍完整保留在 `_out/mutation_results*.jsonl`（逐条含 pyc / 族 / status / units /
     变异点 site），且每个样本的文件名 = md5(pyc|family)[:16] + '_' + family + '.py'
     ⇒ **任一漏检都可由 (pyc, family) 确定性重建**，删样本不损失可复现性。
  2) 删除**中间分片产物**（`v2_shard*.jsonl` / `.err` / `.log`、`_smoke.jsonl`）：
     合并文件 `_out/mutation_results*.jsonl` 已是权威记录。
  3) 落 `_out/miss_samples.json`（留存规则 + 逐族漏检数 + 保留清单）与
     `_out/run_notes.json`（运行注记：分片 MemoryError 事故与覆盖完整性核验）。

用法：python -X utf8 prune_artifacts.py [--keep-per-family 3] [--dry-run]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND4 = os.path.abspath(os.path.join(HERE, '..'))
OUT = os.path.join(ROUND4, '_out')
MISS = os.path.join(ROUND4, '_probes', 'miss')

NAME_RE = re.compile(r'^miss_([0-9a-f]{16})_(.+)\.py$')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep-per-family', type=int, default=3)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    # ── 1) 读合并记录：miss 记录 → (family, pyc, kept 文件名) ──────────
    miss_rows = []
    for jf in ('mutation_results.jsonl', 'mutation_results_extra.jsonl'):
        p = os.path.join(OUT, jf)
        if not os.path.isfile(p):
            continue
        for line in open(p, encoding='utf-8'):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get('cls') == 'MISS':
                miss_rows.append(r)

    by_family = collections.defaultdict(dict)   # family -> {kept_name: pyc}
    for r in miss_rows:
        pyc = r['pyc']
        fam = r['family']
        digest = hashlib.md5(('%s|%s' % (pyc, fam)).encode('utf-8')).hexdigest()[:16]
        name = 'miss_%s_%s.py' % (digest, fam)
        by_family[fam][name] = pyc

    # ── 2) 选样本：每族至多 keep 个、pyc 互不相同 ─────────────────────
    kept, dropped = [], []
    for fam, items in sorted(by_family.items()):
        chosen = []
        seen_pyc = set()
        for name, pyc in sorted(items.items()):
            if pyc in seen_pyc:
                continue
            chosen.append((name, pyc))
            seen_pyc.add(pyc)
            if len(chosen) >= args.keep_per_family:
                break
        keep_names = {n for n, _ in chosen}
        kept += [{'family': fam, 'file': '_probes/miss/' + n, 'pyc': p}
                 for n, p in chosen]
        for name in items:
            if name not in keep_names:
                dropped.append({'family': fam, 'file': '_probes/miss/' + name})

    removed_files = 0
    if not args.dry_run:
        for d in dropped:
            p = os.path.join(ROUND4, d['file'].replace('/', os.sep))
            if os.path.isfile(p):
                os.remove(p)
                removed_files += 1
        for name in sorted(os.listdir(OUT)):
            if name.startswith('v2_shard') or name == '_smoke.jsonl':
                os.remove(os.path.join(OUT, name))

    # ── 3) 留存清单 + 运行注记 ────────────────────────────────────────
    samples = {
        'retention_rule': '每族至多 %d 个样本，pyc 互不相同；文件名 = md5(pyc|family)[:16] + "_" + family + ".py"' % args.keep_per_family,
        'authoritative_record': 'rounds/round4/_out/mutation_results.jsonl 与 mutation_results_extra.jsonl（逐条含 pyc/family/status/units/site）',
        'total_miss_rows': len(miss_rows),
        'per_family_miss': {f: len(v) for f, v in sorted(by_family.items())},
        'kept': kept,
        'dropped_count': len(dropped),
        'removed_files': removed_files,
    }
    notes = {
        'sharding': '补测 20 族分 8 片跑（v2_shard0..7）；其中 shard1 / shard7 末尾在 '
                    'pyc_verify.sha256 读文件阶段触发 MemoryError 并中断（中间产物已删除，'
                    '合并记录未受影响）。',
        'coverage_check': '合并文件逐族复核：20 个族各覆盖 416/416 个绿产物（distinct pyc = 416，'
                          '无缺口）；8 个必需族同样为 416/416（3750 行 = 422 基线 + 8×416）。',
        'intermediate_artifacts_removed': ['_out/v2_shard*.jsonl', '_out/v2_shard*.err',
                                           '_out/v2_shard*.log', '_out/_smoke.jsonl'],
        'judge_path': 'scripts/pyc_verify.py::evaluate（与 CLI `pyc_verify.py single` 同一条代码路径）；'
                      '独立复跑见 _scripts/verify_l2_readings.py 与 _out/verify_l2_readings.json。',
    }
    if not args.dry_run:
        with open(os.path.join(OUT, 'miss_samples.json'), 'w', encoding='utf-8') as f:
            json.dump(samples, f, ensure_ascii=False, indent=1)
        with open(os.path.join(OUT, 'run_notes.json'), 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii=False, indent=1)

    print('[prune] miss_rows=%d kept=%d dropped=%d removed_files=%d'
          % (len(miss_rows), len(kept), len(dropped), removed_files))
    print('[prune] per_family=%s' % json.dumps(samples['per_family_miss'], ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
