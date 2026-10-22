#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：**变异测试实测 v2**（判据漏检率读数，带「判据可见性」分级）。

与 v1 的关键差别（v1 的教训：朴素「变异→漏检」归因会把**惰性变异**算成漏检）：
  * 每次变异额外计算 **judge-visible signature**：用**附件判据本体**的装载与归一化
    （同一 patch 序列 + 同一 CFG 构造）计算「判据看得见的那部分数据」，
    唯一差别是 argval 用**类型敏感**标签（`1` vs `True` vs `1.0` 可分辨）。
  * 分类：
      HARD_MISS   判据**看得见**差异却仍判绿  ⇒ 判据比较算子/归一化有洞（可改进）
      STRUCTURAL  判据**看不见**差异            ⇒ 结构性不可见（须新增判据维度）
      CAUGHT      判据判红
      INVALID     变异产物编译不过（非语义捕获）
      NA          该产物不适用此族

方法：
  1) 语料 = **记录在案 stamps 里的绿产物**（round8 的 batch 报告 + round1 的 rec1_probes_*.json）。
  2) 基线复核：每个语料先跑一次判据本体（`scripts/pyc_verify.py::evaluate`，与 CLI `single`
     同一代码路径），确认当前仍为绿；非绿者剔除。
  3) 变异：对**产物**注入已知语义错误，重跑同一判据，并计算可见性分级。

用法：
  python -X utf8 mutation_experiment2.py --shard 0 --nshards 8
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import py_compile
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND4 = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(ROUND4, '..', '..', '..', '..', '..'))
OUT = os.path.join(ROUND4, '_out')
SCRATCH = os.path.join(ROUND4, '_scratch', 'mut')

sys.path.insert(0, HERE)
import mutation_lib  # noqa: E402
import judge_sig   # noqa: E402


def load_pyc_verify():
    spec = importlib.util.spec_from_file_location(
        'pyc_verify_mod', os.path.join(ROOT, 'scripts', 'pyc_verify.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def corpus_from_stamps():
    """recorded stamps 里 status=success 的 (pyc, product) 对。"""
    out = []
    seen = set()
    rd8 = os.path.join(ROOT, '.trae', 'specs', 'attain-true-completeness', 'rounds', 'round8')
    for name in sorted(os.listdir(rd8)) if os.path.isdir(rd8) else []:
        if not name.endswith('.json'):
            continue
        try:
            d = json.load(open(os.path.join(rd8, name), encoding='utf-8'))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for r in d.get('rows', []):
            if r.get('status') != 'success':
                continue
            key = os.path.abspath(r['pyc'])
            if key in seen:
                continue
            seen.add(key)
            out.append(('r8:' + name, r['pyc'], r['source']))
    r1 = os.path.join(ROOT, '.trae', 'specs', 'attain-true-completeness', 'rounds', 'round1')
    for name in sorted(os.listdir(r1)) if os.path.isdir(r1) else []:
        if not name.startswith('rec1_probes_') or not name.endswith('.json'):
            continue
        try:
            d = json.load(open(os.path.join(r1, name), encoding='utf-8'))
        except Exception:
            continue
        for r in d if isinstance(d, list) else []:
            if r.get('status') != 'success':
                continue
            rel = r.get('pyc_src_rel') or ''
            if not rel or rel.startswith('@'):
                continue
            pyc = os.path.join(ROOT, rel.replace('/', os.sep))
            if not os.path.isfile(pyc):
                continue
            prod = pyc[:-4] + 'OK.py'
            if not os.path.isfile(prod):
                continue
            key = os.path.abspath(pyc)
            if key in seen:
                continue
            seen.add(key)
            out.append(('r1:' + name, pyc, prod))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--nshards', type=int, default=1)
    ap.add_argument('--max-corpus', type=int, default=0, help='0 = 不限')
    ap.add_argument('--families', default='')
    ap.add_argument('--out', default=os.path.join(OUT, 'mutation_results_v2.jsonl'))
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SCRATCH, exist_ok=True)

    done = set()
    if os.path.isfile(args.out):
        for line in open(args.out, encoding='utf-8'):
            try:
                r = json.loads(line)
            except Exception:
                continue
            done.add((r['pyc'], r['family']))

    corpus = corpus_from_stamps()
    probes = [c for c in corpus if c[0].startswith('r1:')]
    bulk = [c for c in corpus if not c[0].startswith('r1:')]
    if args.max_corpus:
        keep = max(0, args.max_corpus - len(probes))
        bulk = bulk[:keep]
    corpus = probes + bulk
    corpus.sort(key=lambda c: (c[0], c[1]))
    shard = [c for i, c in enumerate(corpus) if i % args.nshards == args.shard]
    families = [f for f in (args.families.split(',') if args.families else list(mutation_lib.MUTATIONS))]

    pv = load_pyc_verify()
    compare_pyc = pv.load_compare_pyc(pv.DEFAULT_PYLINGUAL)
    file_sig = judge_sig.load_sig(pv.DEFAULT_PYLINGUAL)
    tmpdir = tempfile.mkdtemp(prefix='l2_mut2_')
    fout = open(args.out, 'a', encoding='utf-8', newline='\n')
    t0 = time.time()
    n_run = 0
    for tag, pyc, prod in shard:
        if (pyc, 'BASELINE') in done:
            continue
        base = pv.evaluate(pyc, prod, tmpdir, compare_pyc)
        fout.write(json.dumps({'pyc': pyc, 'family': 'BASELINE', 'tag': tag,
                               'status': base['status'],
                               'units': [base['units_success'], base['units_total']]},
                              ensure_ascii=False) + '\n')
        fout.flush()
        if base['status'] != 'success':
            continue
        raw = open(prod, 'rb').read()
        try:
            sig_c = file_sig(pyc)
        except Exception as exc:
            sig_c = None
        for fam in families:
            if (pyc, fam) in done:
                continue
            mut, site = mutation_lib.apply_mutation(fam, raw)
            if mut is None:
                fout.write(json.dumps({'pyc': pyc, 'family': fam, 'tag': tag,
                                       'status': 'NA', 'cls': 'NA', 'site': site},
                                      ensure_ascii=False) + '\n')
                fout.flush()
                continue
            mpath = os.path.join(SCRATCH, 'm_%s_%s.py' % (
                hashlib.md5(('%s|%s' % (pyc, fam)).encode('utf-8')).hexdigest()[:16], fam))
            with open(mpath, 'wb') as f:
                f.write(mut)
            # 可见性：把变异产物编译成 pyc，与**原始 pyc** 比「判据看得见的那部分数据」
            visible = None
            try:
                cpath = os.path.join(tmpdir, 'sigmut.pyc')
                py_compile.compile(mpath, cfile=cpath, doraise=True, optimize=0)
                sig_m = file_sig(cpath)
                visible = bool(sig_c is not None and sig_c != sig_m)
            except Exception:
                visible = None
            row = pv.evaluate(pyc, mpath, tmpdir, compare_pyc)
            st = row['status']
            if st == 'success':
                cls = 'HARD_MISS' if visible else 'STRUCTURAL'
            elif st == 'failure':
                cls = 'CAUGHT'
            elif st == 'compile_error':
                cls = 'INVALID'
            else:
                cls = 'JUDGE_ERROR'
            fout.write(json.dumps({'pyc': pyc, 'family': fam, 'tag': tag, 'status': st,
                                   'cls': cls, 'visible': visible,
                                   'units': [row['units_success'], row['units_total']],
                                   'site': site,
                                   'mutated': os.path.relpath(mpath, ROOT).replace('\\', '/'),
                                   'failures': row['failures'][:2]},
                                  ensure_ascii=False) + '\n')
            fout.flush()
            n_run += 1
    fout.close()
    print('[shard %d/%d] corpus=%d judge_runs=%d elapsed=%.1fs -> %s'
          % (args.shard, args.nshards, len(shard), n_run, time.time() - t0, args.out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
