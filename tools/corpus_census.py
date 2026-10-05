#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语料普查与排除反向夹钳（本规范验证面的唯一钉表工具）。

三类口径（合计必须等于 site-packages 下 pyc 总数，无第四类）：
  A 真实语料   = site-packages/**/*.pyc 且文件名不含派生畸形标记，且落在验证面索引里
  B 派生畸形   = 文件名含 `OK.cpython-311`（历史迭代把 *OK.py 再编译成 pyc 再当语料所致）
  C 自造 scratch = 既非 B 也不在索引（名字带 tmp/probe/recomp/OK/_check 痕迹的会话产物）

用法：
  python -X utf8 tools/corpus_census.py                     # 打印读数，A_delta!=0 或出现第四类则退出码 1
  python -X utf8 tools/corpus_census.py --json <out.json>   # 读数 + A/B/C 名单落盘
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, 'site-packages')
JUNK_MARK = 'ok.cpython'          # 小写比对：xxxOK.cpython-311.pyc 之类派生畸形
SCRATCH_HINTS = ('ok', 'tmp', 'temp', 'probe', 'recomp', '_check', 'difffn', 'marker')


def rel(path: str) -> str:
    return os.path.relpath(os.path.abspath(path), CORPUS).replace('\\', '/')


def index_paths(index_files) -> set[str]:
    """索引条目按相对 site-packages 的路径归一，屏蔽 F 盘/工作树前缀差异。"""
    out = set()
    for f in index_files:
        with open(f, encoding='utf-8-sig') as fh:
            for e in json.load(fh):
                p = e['path'].replace('\\', '/')
                if '/site-packages/' in p:
                    out.add(p.split('/site-packages/')[-1])
                else:
                    out.add(rel(p))
    return out


def classify(index: set[str]):
    a, b, c = [], [], []
    for p in sorted(glob.glob(os.path.join(CORPUS, '**', '*.pyc'), recursive=True)):
        r = rel(p)
        if JUNK_MARK in r.lower():
            b.append(r)
        elif r in index:
            a.append(r)
        else:
            c.append(r)
    return a, b, c


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', action='append', default=None,
                    help='验证面索引 json（可多次；默认 = 本规范 baseline/shards 八分片）')
    ap.add_argument('--json', dest='out', default=None)
    args = ap.parse_args()

    shard_dir = os.path.join(ROOT, '.trae', 'specs',
                             'region-reduction-v3-full-corpus-100pct-10rounds', 'baseline', 'shards')
    idx_files = args.index
    if idx_files is None:
        idx_files = sorted(glob.glob(os.path.join(shard_dir, 'shard*.json')))
        if not idx_files:
            print('[fatal] 默认验证面索引缺失：%s' % shard_dir)
            return 1
    index = index_paths(idx_files)

    a, b, c = classify(index)
    total = len(a) + len(b) + len(c)
    a_delta = len(index ^ set(a))          # 索引与 A 类的对称差
    on_disk_missing = sorted(p for p in index if not os.path.isfile(os.path.join(CORPUS, p.replace('/', os.sep))))
    products = [p for p in a if os.path.isfile(os.path.join(CORPUS, p[:-4] + 'OK.py'))]

    print('total=%d A=%d B=%d C=%d A_delta=%d' % (total, len(a), len(b), len(c), a_delta))
    print('index_entries=%d products_ok=%d/%d missing_pyc=%d'
          % (len(index), len(products), len(a), len(on_disk_missing)))
    if c:
        print('C 类（不在验证面且非派生畸形）名单：')
        for p in c:
            print('  %s' % p)
    if on_disk_missing:
        print('索引有但盘上没有的条目：')
        for p in on_disk_missing:
            print('  %s' % p)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps({
                'snapshot_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'corpus_root': CORPUS.replace('\\', '/'),
                'index_files': [x.replace('\\', '/') for x in idx_files],
                'total': total, 'A': len(a), 'B': len(b), 'C': len(c),
                'A_delta': a_delta, 'products_ok': len(products),
                'A_roster': a, 'B_roster': b, 'C_roster': c,
                'index_missing_on_disk': on_disk_missing,
            }, ensure_ascii=False, indent=1) + '\n')
        print('-> %s' % args.out)

    return 0 if a_delta == 0 and not on_disk_missing else 1


if __name__ == '__main__':
    sys.exit(main())
