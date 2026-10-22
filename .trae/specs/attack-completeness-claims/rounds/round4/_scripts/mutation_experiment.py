#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：**变异测试实测**（判据漏检率读数）——round4 正式驱动器。

方法（与 `scripts/pyc_verify.py::evaluate` 同一条判据代码路径）：
  1) 语料 = **记录在案（recorded stamps）的绿产物**：
     - `.trae/specs/attain-true-completeness/rounds/round8/*report*.json`
       （402 语料八分片 + small34 + quotation 的 success 行）
     - `.trae/specs/attain-true-completeness/rounds/round1/rec1_probes_*.json`
       （登记探针的 success 行）
  2) 基线复核：对每个语料先跑一次**判据本体**，确认当前仍为绿；非绿者剔除。
  3) 变异：对**产物**注入已知语义错误（`mutation_lib`），重跑同一判据。
     - status=success      ⇒ **漏检 MISS**：语义已错，判据仍判绿
     - status=failure      ⇒ **捕获 CAUGHT**
     - status=compile_error⇒ 变异产物不可编译（非语义捕获，单列 INVALID）
     - status=error        ⇒ 判据异常（单列 JUDGE_ERROR）
     - 'NA'                ⇒ 该产物不适用此族（不计入分母）
  4) 产物：`_out/mutation_results.jsonl`（增量可续跑）+ `_out/mutation_summary.json`

分片：--shard i --nshards n（可多次调用拼接；结果按 jsonl 追加去重）。
变异文件默认写到 **仓库外**临时目录（可复现：文件名 = md5(pyc|family)[:16] + 族名）；
需要留证时用 `--keep-misses` 把漏检样本复制到 `_probes/miss/`。

用法：
  python -X utf8 mutation_experiment.py --shard 0 --nshards 8 --families a_num_int,...
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND4 = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(ROUND4, '..', '..', '..', '..', '..'))
OUT = os.path.join(ROUND4, '_out')

sys.path.insert(0, HERE)
import mutation_lib  # noqa: E402


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
    ap.add_argument('--probe-only', action='store_true', help='只用 round1 登记探针')
    ap.add_argument('--families', default='')
    ap.add_argument('--scratch', default=os.path.join(ROUND4, '_scratch', 'mut'))
    ap.add_argument('--out', default=os.path.join(OUT, 'mutation_results.jsonl'))
    ap.add_argument('--keep-misses', action='store_true', help='把漏检样本复制到 _probes/miss/')
    ap.add_argument('--reset', action='store_true', help='清空输出 jsonl 后重跑')
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(args.scratch, exist_ok=True)
    miss_dir = os.path.join(ROUND4, '_probes', 'miss')
    if args.keep_misses:
        os.makedirs(miss_dir, exist_ok=True)

    if args.reset and os.path.isfile(args.out):
        os.remove(args.out)

    done = set()
    baselines = {}
    if os.path.isfile(args.out):
        for line in open(args.out, encoding='utf-8'):
            try:
                r = json.loads(line)
            except Exception:
                continue
            done.add((r['pyc'], r['family']))
            if r['family'] == 'BASELINE':
                baselines[r['pyc']] = r['status']

    corpus = corpus_from_stamps()
    if args.probe_only:
        corpus = [c for c in corpus if c[0].startswith('r1:')]
    probes = [c for c in corpus if c[0].startswith('r1:')]
    bulk = [c for c in corpus if not c[0].startswith('r1:')]
    if args.max_corpus:
        keep = max(0, args.max_corpus - len(probes))
        bulk = bulk[:keep]
    corpus = probes + bulk
    corpus.sort(key=lambda c: (c[0], c[1]))

    shard = [c for i, c in enumerate(corpus) if i % args.nshards == args.shard]
    families = [f for f in (args.families.split(',') if args.families
                             else mutation_lib.REQUIRED_FAMILIES)]

    pv = load_pyc_verify()
    compare_pyc = pv.load_compare_pyc(pv.DEFAULT_PYLINGUAL)
    tmpdir = tempfile.mkdtemp(prefix='l2_mut_')
    fout = open(args.out, 'a', encoding='utf-8', newline='\n')
    t0 = time.time()
    n_run = 0
    n_miss = 0
    for tag, pyc, prod in shard:
        if (pyc, 'BASELINE') in done:
            base_status = baselines.get(pyc)
        else:
            base = pv.evaluate(pyc, prod, tmpdir, compare_pyc)
            base_status = base['status']
            baselines[pyc] = base_status
            fout.write(json.dumps({'pyc': pyc, 'family': 'BASELINE', 'tag': tag,
                                   'status': base['status'],
                                   'units': [base['units_success'], base['units_total']]},
                                  ensure_ascii=False) + '\n')
            fout.flush()
        if base_status != 'success':
            continue
        raw = open(prod, 'rb').read()
        for fam in families:
            if (pyc, fam) in done:
                continue
            mut, site = mutation_lib.apply_mutation(fam, raw)
            if mut is None:
                fout.write(json.dumps({'pyc': pyc, 'family': fam, 'tag': tag,
                                       'status': 'NA', 'site': site}, ensure_ascii=False) + '\n')
                fout.flush()
                continue
            digest = hashlib.md5(('%s|%s' % (pyc, fam)).encode('utf-8')).hexdigest()[:16]
            mpath = os.path.join(args.scratch, 'm_%s_%s.py' % (digest, fam))
            with open(mpath, 'wb') as f:
                f.write(mut)
            row = pv.evaluate(pyc, mpath, tmpdir, compare_pyc)
            rec = {'pyc': pyc, 'family': fam, 'tag': tag, 'status': row['status'],
                   'units': [row['units_success'], row['units_total']],
                   'site': site, 'mutated': mpath}
            if row['status'] == 'success':
                rec['cls'] = 'MISS'
                n_miss += 1
                if args.keep_misses:
                    keep = os.path.join(miss_dir, 'miss_%s_%s.py' % (digest, fam))
                    shutil.copyfile(mpath, keep)
                    rec['kept'] = os.path.relpath(keep, ROOT).replace('\\', '/')
            elif row['status'] == 'failure':
                rec['cls'] = 'CAUGHT'
                rec['failures'] = row['failures'][:2]
            elif row['status'] == 'compile_error':
                rec['cls'] = 'INVALID'
            else:
                rec['cls'] = 'JUDGE_ERROR'
            fout.write(json.dumps(rec, ensure_ascii=False) + '\n')
            fout.flush()
            n_run += 1
    fout.close()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print('[shard %d/%d] corpus=%d judge_runs=%d miss=%d elapsed=%.1fs -> %s'
          % (args.shard, args.nshards, len(shard), n_run, n_miss,
             time.time() - t0, args.out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
