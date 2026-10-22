#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：**判据漏检率实测**（任务约定口径）。

判据调用方式严格按任务约定，**只走 CLI**：

    python -X utf8 scripts/pyc_verify.py single <pyc> --source <变异产物>

本脚本**不复用** `scripts/pyc_verify.py` 的内部 `evaluate()` API（那只是省进程开销），
而是把使用者实际会敲的那条命令原样跑起来 ⇒ 读数与「人敲命令看到的 status」一致。

流程：
  1) 语料 = **记录在案（recorded stamps）的绿产物**
     （`attain-true-completeness/rounds/round8/*report*.json` 与
       `attain-true-completeness/rounds/round1/rec1_probes_*.json` 的 success 行）；
  2) 基线复核：对每个产物先跑一次 CLI，确认当前仍为绿（status=success）；
     非绿者剔除（不入分母）；
  3) 注入语义错误（`_scripts/mutation_lib.py`，CPython ast 定位 + UTF-8 字节切片），
     重跑同一 CLI；
  4) 分类：
       status=success       ⇒ **MISS（漏检）**：语义已错，判据仍判绿
       status=failure       ⇒ CAUGHT（捕获）
       status=compile_error ⇒ INVALID（变异产物不可编译，非语义捕获）
       status=error         ⇒ JUDGE_ERROR（判据异常）
       变异不适用            ⇒ NA（不计入分母）

输出：
  `_out/mutate_parts/part_<shard>.jsonl`  逐次判定的原始记录
  `_out/mutate_summary.json`               汇总（mutated / missed / miss_rate）
  `_probes/miss_cli/miss_*.py`             漏检样本（可选，`--keep-misses`）

用法：
  python -X utf8 mutate.py --shard 0 --nshards 32
  python -X utf8 mutate.py --summary
  python -X utf8 mutate.py --families d_int_to_bool --max-products 20
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND4 = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(ROUND4, '..', '..', '..', '..', '..'))
OUT = os.path.join(ROUND4, '_out')
PARTS = os.path.join(OUT, 'mutate_parts')
SCRATCH = os.path.join(ROUND4, '_scratch', 'mutate')
MISS_DIR = os.path.join(ROUND4, '_probes', 'miss_cli')

sys.path.insert(0, HERE)
import mutation_lib  # noqa: E402  （同目录的语义变异族库）

STATUS_RE = re.compile(r'\[single\]\s+status=(\w+)\s+units=(\d+)/(\d+)')

# 任务要求的 8 类（与 mutation_lib.REQUIRED_FAMILIES 同序、同语义）
REQUIRED_FAMILIES = list(mutation_lib.REQUIRED_FAMILIES)

FAMILY_LABELS = {
    'a_num_int': '(a) 改数值：整数字面量 n -> n+1',
    'b_cmp_polarity': '(b) 翻转比较：a<b <-> a>b（<=/>= 同理）',
    'c_del_assign': '(c) 删语句：删除一条赋值语句',
    'd_int_to_bool': '(d) x=1 改 x=True（纯类型变，值不变）',
    'e_str_content': '(e) 改字符串：字符串字面量内容 +X',
    'f_stmt_swap': '(f) 换语句序：交换两条相互独立的赋值语句',
    'g_rename_local': '(g) 改标识符：函数内形参/局部一致改名',
    'h_arg_swap': '(h) 换实参序：交换同一调用的两个实参',
}


# ── 语料发现（记录在案的绿产物）───────────────────────────────────────────────


def corpus_from_stamps():
    """recorded stamps 里 status=success 的 (tag, pyc, product) 对，按路径去重。"""
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
            out.append(('r8:' + name, os.path.abspath(r['pyc']), os.path.abspath(r['source'])))
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
            pyc = os.path.abspath(os.path.join(ROOT, rel.replace('/', os.sep)))
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
    out.sort(key=lambda c: (c[0], c[1]))
    return out


# ── 判据调用（只用 CLI `single` 子命令）──────────────────────────────────────


def run_judge(pyc: str, source: str, timeout: int = 180):
    """跑 `python -X utf8 scripts/pyc_verify.py single <pyc> --source <source>`。

    返回 (status, units_success, units_total, stdout_tail, elapsed_sec)。
    status 取自 CLI 自己打印的 `[single] status=...`，与判定本体语义一致。
    """
    cmd = [sys.executable, '-X', 'utf8', os.path.join('scripts', 'pyc_verify.py'),
           'single', pyc, '--source', source]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=timeout)
    except subprocess.TimeoutExpired:
        return 'TIMEOUT', 0, 0, 'timeout after %ds' % timeout, time.time() - t0
    out = (p.stdout or '') + (p.stderr or '')
    m = STATUS_RE.search(out)
    el = time.time() - t0
    if not m:
        return 'NO_STATUS', 0, 0, out.strip()[-300:], el
    return m.group(1), int(m.group(2)), int(m.group(3)), out.strip()[-300:], el


def ruler_stamp():
    """判据本体的 sha256 前 16 位（与 pyc_verify.ruler_stamp 同口径），保证读数可追溯。"""
    eq = os.path.join(r'D:\Desktop\ptrade相关\pylingual', 'pylingual', 'equivalence_check.py')
    if not os.path.isfile(eq):
        return {'compare_pyc': eq, 'compare_pyc_sha256': None}
    h = hashlib.sha256()
    with open(eq, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return {'compare_pyc': eq.replace('\\', '/'),
            'compare_pyc_sha256': h.hexdigest()[:16]}


# ── 变异产物命名（可复现：md5(pyc|family)[:16] + 族名）────────────────────────


def mut_path(digest: str, fam: str) -> str:
    return os.path.join(SCRATCH, 'm_%s_%s.py' % (digest, fam))


def digest_of(pyc: str, fam: str) -> str:
    return hashlib.md5(('%s|%s' % (pyc, fam)).encode('utf-8')).hexdigest()[:16]


# ── 主流程 ────────────────────────────────────────────────────────────────────


def load_prior_baselines(path):
    """从同轮既有记录里读 BASELINE 判定（同一 compare_pyc 代码路径），用于免去重复基线调用。

    返回 {pyc: status}；只有 status='success' 的记录会被采用。
    """
    out = {}
    if not path or not os.path.isfile(path):
        return out
    for line in open(path, encoding='utf-8'):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get('family') != 'BASELINE':
            continue
        out[os.path.abspath(r['pyc'])] = r.get('status')
    return out


def cmd_run(args):
    os.makedirs(PARTS, exist_ok=True)
    os.makedirs(SCRATCH, exist_ok=True)
    if args.keep_misses:
        os.makedirs(MISS_DIR, exist_ok=True)

    corpus = corpus_from_stamps()
    if args.sample_mod > 1:
        corpus = [c for i, c in enumerate(corpus) if i % args.sample_mod == args.sample_offset]
    if args.max_products:
        corpus = corpus[:args.max_products]
    shard = [c for i, c in enumerate(corpus) if i % args.nshards == args.shard]
    families = [f.strip() for f in args.families.split(',') if f.strip()] or REQUIRED_FAMILIES

    out_path = os.path.join(PARTS, 'part_%02d.jsonl' % args.shard)
    done = set()
    if os.path.isfile(out_path):
        for line in open(out_path, encoding='utf-8'):
            try:
                r = json.loads(line)
            except Exception:
                continue
            done.add((r['pyc'], r['family']))

    fout = open(out_path, 'a', encoding='utf-8', newline='\n')
    t0 = time.time()
    n_run = n_miss = 0
    counted = {}
    stop = False
    prior_baselines = load_prior_baselines(args.baseline_source)
    for tag, pyc, prod in shard:
        if stop:
            break
        if not os.path.isfile(prod):
            continue
        # 基线复核（每个产物只做一次）：
        #   默认跑一次 CLI 确认仍为绿（非绿者剔除，不入分母）；
        #   若提供了 --baseline-source（同轮既有 BASELINE 记录，同一 compare_pyc 代码路径），
        #   则采用其判定以免重复调用（provenance 字段如实标注来源）。
        if (pyc, 'BASELINE') in done:
            green = True                      # 本分片此前已判定（已落盘）
        else:
            prior = prior_baselines.get(os.path.abspath(pyc))
            if prior is not None and args.baseline_source:
                st, us, ut = prior, 0, 0
                src = 'prior-round'
            else:
                st, us, ut, tail, el = run_judge(pyc, prod)
                src = 'cli'
            done.add((pyc, 'BASELINE'))
            fout.write(json.dumps({'pyc': pyc, 'product': prod, 'family': 'BASELINE',
                                   'tag': tag, 'status': st, 'units': [us, ut],
                                   'provenance': src}, ensure_ascii=False) + '\n')
            fout.flush()
            green = (st == 'success')
        if not green:
            continue                          # 非绿 ⇒ 剔除，不入分母
        try:
            raw = open(prod, 'rb').read()
        except OSError:
            continue
        for fam in families:
            if stop:
                break
            if (pyc, fam) in done:
                continue
            mut, site = mutation_lib.apply_mutation(fam, raw)
            if mut is None:
                done.add((pyc, fam))
                fout.write(json.dumps({'pyc': pyc, 'product': prod, 'family': fam,
                                       'tag': tag, 'status': 'NA', 'cls': 'NA',
                                       'site': site}, ensure_ascii=False) + '\n')
                fout.flush()
                continue
            dg = digest_of(pyc, fam)
            mp = mut_path(dg, fam)
            with open(mp, 'wb') as f:
                f.write(mut)
            st, us, ut, tail, el = run_judge(pyc, mp)
            cls = {'success': 'MISS', 'failure': 'CAUGHT',
                   'compile_error': 'INVALID', 'error': 'JUDGE_ERROR'}.get(st, 'JUDGE_ERROR')
            rec = {'pyc': pyc, 'product': prod, 'family': fam, 'tag': tag,
                   'status': st, 'cls': cls, 'units': [us, ut], 'site': site,
                   'mutated': os.path.relpath(mp, ROOT).replace('\\', '/'),
                   'elapsed': round(el, 2)}
            done.add((pyc, fam))
            fout.write(json.dumps(rec, ensure_ascii=False) + '\n')
            fout.flush()
            n_run += 1
            if cls == 'MISS':
                n_miss += 1
                if args.keep_misses:
                    # 全局每族最多留 3 个样本（跨分片计数，避免多分片重复留存）
                    if fam not in counted:
                        counted[fam] = sum(1 for n in os.listdir(MISS_DIR)
                                           if n.endswith('_%s.py' % fam))
                    if counted[fam] < 3:
                        counted[fam] += 1
                        shutil.copyfile(mp, os.path.join(MISS_DIR, 'miss_%s_%s.py' % (dg, fam)))
            if time.time() - t0 > args.time_budget:
                stop = True
                break
    fout.close()
    meta = {'shard': args.shard, 'nshards': args.nshards, 'corpus_in_shard': len(shard),
            'sample_mod': args.sample_mod, 'sample_offset': args.sample_offset,
            'families': families, 'judge_runs': n_run, 'miss': n_miss,
            'elapsed': round(time.time() - t0, 1), 'out': out_path}
    with open(os.path.join(PARTS, 'meta_%02d.json' % args.shard), 'w',
              encoding='utf-8', newline='\n') as mf:
        mf.write(json.dumps(meta, ensure_ascii=False, indent=1, sort_keys=True) + '\n')
    print('[shard %d/%d] corpus=%d judge_runs=%d miss=%d elapsed=%.1fs -> %s'
          % (args.shard, args.nshards, len(shard), n_run, n_miss,
             time.time() - t0, out_path))
    return 0


def cmd_summary(args):
    scope_corpus = corpus_from_stamps()
    if args.scope_mod > 1:
        scope_corpus = [c for i, c in enumerate(scope_corpus)
                        if i % args.scope_mod == args.scope_offset]
    scope = {os.path.abspath(c[1]) for c in scope_corpus}
    rows = []
    parts = sorted(os.listdir(PARTS)) if os.path.isdir(PARTS) else []
    for name in parts:
        if not name.endswith('.jsonl'):
            continue
        for line in open(os.path.join(PARTS, name), encoding='utf-8'):
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    seen = set()
    uniq = []
    for r in rows:
        if scope and os.path.abspath(r['pyc']) not in scope:
            continue
        k = (r['pyc'], r['family'])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    # 落盘「作用域内」的逐次判定原始记录（汇总的唯一数据源）
    uniq.sort(key=lambda r: (r['family'], r['pyc']))
    scoped_path = os.path.join(OUT, 'mutate_results.jsonl')
    with open(scoped_path, 'w', encoding='utf-8', newline='\n') as f:
        for r in uniq:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    baselines = [r for r in uniq if r['family'] == 'BASELINE']
    green = [r for r in baselines if r['status'] == 'success']
    prov = {}
    for r in baselines:
        p = r.get('provenance', 'cli')
        prov[p] = prov.get(p, 0) + 1
    fam_rows = {}
    for r in uniq:
        if r['family'] == 'BASELINE':
            continue
        fam_rows.setdefault(r['family'], []).append(r)

    families = []
    tot_mut = tot_miss = 0
    for fam in REQUIRED_FAMILIES + [f for f in fam_rows if f not in REQUIRED_FAMILIES]:
        rs = fam_rows.get(fam, [])
        na = sum(1 for r in rs if r.get('cls') == 'NA' or r.get('status') == 'NA')
        applied = [r for r in rs if r.get('cls') in ('MISS', 'CAUGHT', 'INVALID', 'JUDGE_ERROR')]
        mutated = len(applied)
        missed = sum(1 for r in applied if r['cls'] == 'MISS')
        caught = sum(1 for r in applied if r['cls'] == 'CAUGHT')
        invalid = sum(1 for r in applied if r['cls'] == 'INVALID')
        jerr = sum(1 for r in applied if r['cls'] == 'JUDGE_ERROR')
        rate = (missed / mutated) if mutated else None
        fam_miss_paths = sorted({r['pyc'] for r in applied if r['cls'] == 'MISS'})
        families.append({
            'family': fam, 'label': FAMILY_LABELS.get(fam, fam),
            'required': fam in REQUIRED_FAMILIES,
            'mutated': mutated, 'missed': missed, 'miss_rate': rate,
            'caught': caught, 'invalid': invalid, 'judge_error': jerr, 'na': na,
            'miss_examples': fam_miss_paths[:8],
        })
        if fam in REQUIRED_FAMILIES:
            tot_mut += mutated
            tot_miss += missed

    metas = []
    for name in sorted(os.listdir(PARTS)) if os.path.isdir(PARTS) else []:
        if name.startswith('meta_') and name.endswith('.json'):
            try:
                metas.append(json.load(open(os.path.join(PARTS, name), encoding='utf-8')))
            except Exception:
                continue
    sample_mods = sorted({m.get('sample_mod', 1) for m in metas})
    summary = {
        'judge_command': 'python -X utf8 scripts/pyc_verify.py single <pyc> --source <mutated>',
        'ruler': ruler_stamp(),
        'interpreter': sys.version.split()[0],
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'sample_mod': args.scope_mod if args.scope_mod > 1 else 1,
        'scope_products': len(scope_corpus),
        'scope_records': len(uniq),
        'scope_results_jsonl': os.path.relpath(scoped_path, ROOT).replace('\\', '/'),
        'n_shards': len(metas),
        'shard_meta': metas,
        'baseline_total': len(baselines),
        'baseline_green': len(green),
        'baseline_provenance': prov,
        'required_families': REQUIRED_FAMILIES,
        'families': families,
        'required_total_mutated': tot_mut,
        'required_total_missed': tot_miss,
        'required_miss_rate': (tot_miss / tot_mut) if tot_mut else None,
        'total_mutated': sum(f['mutated'] for f in families),
        'total_missed': sum(f['missed'] for f in families),
        'overall_miss_rate': (sum(f['missed'] for f in families)
                              / sum(f['mutated'] for f in families)) if families else None,
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'mutate_summary.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + '\n')

    print('baseline: %d judged, %d still green (provenance %s)'
          % (len(baselines), len(green), prov))
    print('%-18s %8s %8s %10s  %s' % ('family', 'mutated', 'missed', 'miss-rate', 'label'))
    for f_ in families:
        rate = '-' if f_['miss_rate'] is None else '%.2f%%' % (100 * f_['miss_rate'])
        print('%-18s %8d %8d %10s  %s'
              % (f_['family'], f_['mutated'], f_['missed'], rate, f_['label']))
    print('%-18s %8d %8d %10s' % ('REQUIRED TOTAL', tot_mut, tot_miss,
                                   '-' if not tot_mut else '%.2f%%' % (100 * tot_miss / tot_mut)))
    return 0


def main():
    ap = argparse.ArgumentParser(description='L2 判定层：CLI 口径的语义变异漏检率实测')
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--nshards', type=int, default=1)
    ap.add_argument('--families', default='')
    ap.add_argument('--max-products', type=int, default=0)
    ap.add_argument('--sample-mod', type=int, default=1,
                    help='确定性子采样：取语料中 index %% sample_mod == sample_offset 的条目')
    ap.add_argument('--sample-offset', type=int, default=0)
    ap.add_argument('--time-budget', type=float, default=240.0,
                    help='单次调用的墙钟预算（秒），保证命令在时限内收尾')
    ap.add_argument('--keep-misses', action='store_true')
    ap.add_argument('--baseline-source', default='',
                    help='同轮既有 BASELINE 记录 jsonl（同一 compare_pyc 路径），'
                         '提供后基线判定直接采用该记录，不再重复调用 CLI')
    ap.add_argument('--summary', action='store_true', help='合并分片并产出汇总')
    ap.add_argument('--scope-mod', type=int, default=1,
                    help='汇总口径的确定性子采样（与运行时 --sample-mod 同一口径）')
    ap.add_argument('--scope-offset', type=int, default=0)
    args = ap.parse_args()
    if args.summary:
        return cmd_summary(args)
    return cmd_run(args)


if __name__ == '__main__':
    sys.exit(main())
