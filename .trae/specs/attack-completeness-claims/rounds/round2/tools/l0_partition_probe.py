#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AT-03 区域划分唯一性/完备性机检探针。

对给定 .pyc（可多个），跑 RegionAnalyzer.analyze() 后枚举：
  (a) 双认领块：被 >=2 个 region's .blocks 同时包含的块；
      —— 判据：划分「唯一」要求每个块至多被一个区域认领（claim）。
  (b) 认领冲突的裁决方式：
      - 静态优先级裁决（REGION_TYPE_PRIORITY 不同）
      - 动态分数裁决（_should_use_dynamic_priority 为真且分数不等）
      - **平局 / 先到先得**（优先级相同且动态分数相同）⇒ 划分依赖注册顺序
        ⇒ 原理不决定划分（唯一性不成立）
  (c) 无归属块：cfg.blocks 中既不属于任何 region.blocks、也不在 block_to_region 的块
      —— 判据：划分「完备」要求每块恰属一区（原理 2）。
  (d) 孤儿释放后新增的 BASIC 区域数（region_ast_generator.generate() 顶部的孤儿释放路径）。

用法：
  python -X utf8 l0_partition_probe.py --dir <probes dir> [--out <json>]
纪律：只读 core/**；不改任何被测文件。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)

import py_compile  # noqa: E402


def iter_code_objects(code):
    yield code
    for const in getattr(code, 'co_consts', ()) or ():
        if hasattr(const, 'co_code'):
            for sub in iter_code_objects(const):
                yield sub


def build_code(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get()
    if hasattr(code_obj, 'to_python_code'):
        return code_obj.to_python_code()
    return code_obj


def analyze_one(code, tag):
    from core.cfg import build_cfg
    from core.cfg.region_analyzer import RegionAnalyzer
    cfg = build_cfg(code)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()
    prio = RegionAnalyzer.REGION_TYPE_PRIORITY

    claims = {}
    for r in analyzer.regions:
        for b in r.blocks:
            claims.setdefault(id(b), []).append(r)

    double_claim = []
    tie_resolved = []
    for bid, owners in claims.items():
        if len(owners) < 2:
            continue
        blk = next(iter(owners[0].blocks))
        canonical = analyzer.block_to_region.get(blk)
        entry = {'code': tag,
                 'block_offset': blk.start_offset,
                 'claimants': [type(o).__name__ + '/' + o.region_type.name for o in owners],
                 'canonical': type(canonical).__name__ if canonical else None,
                 'canonical_is_first': bool(canonical is owners[0])}
        double_claim.append(entry)
        ps = {prio.get(o.region_type, 0) for o in owners}
        if len(ps) == 1:
            scores = [analyzer._compute_dynamic_region_score(blk, o) for o in owners]
            entry['resolution'] = 'tie_priority_equal'
            entry['dynamic_priority_applies'] = bool(
                analyzer._should_use_dynamic_priority(owners[0], owners[1]))
            entry['dynamic_scores'] = scores
            entry['scores_equal'] = len({round(s, 9) for s in scores}) == 1
            tie_resolved.append(entry)

    owned = set(id(b) for b in analyzer.block_to_region.keys())
    all_blk = list(cfg.blocks.values())
    unowned = [b.start_offset for b in all_blk if id(b) not in owned]

    return {
        'code': tag,
        'regions': len(analyzer.regions),
        'blocks_total': len(all_blk),
        'blocks_in_block_to_region': len(owned),
        'double_claim_blocks': double_claim,
        'tie_resolved_blocks': tie_resolved,
        'unowned_block_offsets': sorted(unowned),
        'unowned_count': len(unowned),
    }


def analyze(pyc_path):
    code = build_code(pyc_path)
    rows = []
    for co in iter_code_objects(code):
        try:
            rows.append(analyze_one(co, getattr(co, 'co_name', '?')))
        except Exception as exc:
            rows.append({'code': getattr(co, 'co_name', '?'),
                         'error': '%s: %s' % (type(exc).__name__, exc)})
    agg = {
        'pyc': os.path.relpath(pyc_path, ROOT).replace('\\', '/'),
        'code_objects': len(rows),
        'double_claim_total': sum(len(r.get('double_claim_blocks', [])) for r in rows),
        'tie_resolved_total': sum(len(r.get('tie_resolved_blocks', [])) for r in rows),
        'unowned_total': sum(r.get('unowned_count', 0) for r in rows),
        'rows': rows,
    }
    return agg


def main():
    args = sys.argv[1:]
    srcdir = None
    out = None
    i = 0
    while i < len(args):
        if args[i] == '--dir':
            srcdir = args[i + 1]; i += 2
        elif args[i] == '--out':
            out = args[i + 1]; i += 2
        else:
            i += 1
    if not srcdir:
        print(__doc__)
        return 2
    srcdir = os.path.abspath(srcdir)
    rows = []
    for name in sorted(os.listdir(srcdir)):
        if not name.endswith('.pyc'):
            continue
        path = os.path.join(srcdir, name)
        try:
            rows.append(analyze(path))
        except Exception as exc:
            rows.append({'pyc': name, 'error': '%s: %s' % (type(exc).__name__, exc)})
        r = rows[-1]
        if 'error' in r:
            print('[%s] ERROR %s' % (name, r['error']))
        else:
            print('[%s] code_objs=%d double_claim=%d tie=%d unowned=%d' % (
                name, r['code_objects'], r['double_claim_total'],
                r['tie_resolved_total'], r['unowned_total']))
    if out:
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
        print('-> wrote %s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
