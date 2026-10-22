#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 语料外差分驱动（§2）。

对每个语料外样本：
  1. 把原始 .pyc 复制到 rounds/round6/offcorpus/<slug>.pyc（只读原件，不改原件）
  2. `python -X utf8 pycdc.py <pyc> -o <base>OK.py`  -> 产物
  3. `python -X utf8 scripts/pyc_verify.py single <pyc> --source <产物>` -> 判据读数
  4. 额外核对：**源码**（.py）与 **原件 .pyc** 的字节码是否一致
     （`src_matches_pyc`）：不一致时该样本的「源码语义」不能代表「pyc 语义」，
     §2 的语义差分结论必须以 pyc 为准并显式声明。

输出：JSON（--out）。每条记录：
  {slug, src, pyc_src, pyc_copy, product, features, origin,
   pycdc: {rc, elapsed, timeout, stderr_tail},
   verify: {status, units_success, units_total, failures, elapsed},
   src_matches_pyc: bool|null, notes: [...]}

约束：
  * 单条样本的每个子命令都有独立超时（默认 150s）；外层用 --start/--count 分块，
    保证每次调用 <=300s。
  * 只写 rounds/round6/ 之下。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND6 = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(ROUND6, '..', '..', '..', '..', '..'))
OUTDIR = os.path.join(ROUND6, 'offcorpus')


def sha256(path: str, n: int = 64) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()[:n]


def run(cmd, timeout: int, cwd=None) -> dict:
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                           errors='replace', timeout=timeout, cwd=cwd or REPO)
        return {'rc': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr,
                'elapsed': round(time.time() - t0, 1), 'timeout': False}
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ''
        err = exc.stderr or ''
        if isinstance(out, bytes):
            out = out.decode('utf-8', 'replace')
        if isinstance(err, bytes):
            err = err.decode('utf-8', 'replace')
        return {'rc': None, 'stdout': out, 'stderr': err,
                'elapsed': round(time.time() - t0, 1), 'timeout': True}


def parse_verify(out: str) -> dict:
    """解析 pyc_verify.py single 的 stdout。"""
    row = {'status': None, 'units_success': None, 'units_total': None, 'failures': []}
    for line in out.splitlines():
        s = line.strip()
        if s.startswith('[single] status='):
            for part in s.split():
                if part.startswith('status='):
                    row['status'] = part.split('=', 1)[1]
                elif part.startswith('units='):
                    v = part.split('=', 1)[1]
                    if '/' in v:
                        a, b = v.split('/')
                        row['units_success'] = int(a)
                        row['units_total'] = int(b)
        if line.startswith('  ') and s and not s.startswith('[single]'):
            row['failures'].append(s)
    return row


def code_tree(code):
    """递归收集 (name, co_code)。"""
    out = [(code.co_name, code.co_code)]
    for c in code.co_consts:
        if hasattr(c, 'co_code'):
            out.extend(code_tree(c))
    return out


def source_matches_pyc(src: str, pyc: str):
    """核对 .py 重新编译后的字节码是否与原件 .pyc 一致。"""
    try:
        import marshal
        import py_compile
        import tempfile
        with open(pyc, 'rb') as f:
            f.read(16)
            orig = marshal.load(f)
        with tempfile.TemporaryDirectory() as td:
            cpath = os.path.join(td, 'x.pyc')
            py_compile.compile(src, cfile=cpath, doraise=True, optimize=0)
            with open(cpath, 'rb') as f:
                f.read(16)
                recomp = marshal.load(f)
        a = code_tree(orig)
        b = code_tree(recomp)
        if len(a) != len(b):
            return False
        return all(x[0] == y[0] and x[1] == y[1] for x, y in zip(a, b))
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--samples', required=True, help='样本清单 JSON')
    ap.add_argument('--out', required=True)
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--count', type=int, default=8)
    ap.add_argument('--timeout', type=int, default=150)
    ap.add_argument('--no-source-check', action='store_true')
    args = ap.parse_args()

    samples = json.load(open(args.samples, encoding='utf-8'))['samples']
    os.makedirs(OUTDIR, exist_ok=True)
    rows = []
    sel = samples[args.start:args.start + args.count]
    for s in sel:
        slug = s['slug']
        copy_pyc = os.path.join(OUTDIR, slug + '.pyc')
        product = os.path.join(OUTDIR, slug + 'OK.py')
        shutil.copyfile(s['pyc'], copy_pyc)
        if os.path.exists(product):
            os.remove(product)
        rec = {'slug': slug, 'src': s.get('src'), 'pyc_src': s['pyc'],
               'pyc_copy': copy_pyc, 'product': product,
               'features': s.get('features', []), 'origin': s.get('origin'),
               'notes': []}
        d = run([sys.executable, '-X', 'utf8', 'pycdc.py', copy_pyc, '-o', product],
                timeout=args.timeout)
        rec['pycdc'] = {'rc': d['rc'], 'elapsed': d['elapsed'], 'timeout': d['timeout'],
                        'stderr_tail': d['stderr'][-800:]}
        if d['timeout']:
            rec['notes'].append('pycdc 超时（未产出完整产物）')
        if not os.path.exists(product):
            rec['notes'].append('pycdc 未产出文件')
        if os.path.exists(product):
            v = run([sys.executable, '-X', 'utf8', 'scripts/pyc_verify.py', 'single',
                     copy_pyc, '--source', product], timeout=args.timeout)
            row = parse_verify(v['stdout'])
            row.update({'rc': v['rc'], 'elapsed': v['elapsed'], 'timeout': v['timeout'],
                        'stderr_tail': v['stderr'][-400:]})
            rec['verify'] = row
        else:
            rec['verify'] = {'status': 'no_product'}
        if not args.no_source_check and s.get('src') and os.path.exists(s['src']):
            rec['src_matches_pyc'] = source_matches_pyc(s['src'], s['pyc'])
            if rec['src_matches_pyc'] is False:
                rec['notes'].append('源码与原件 pyc 字节码不一致 => 语义核对以 pyc 为准')
        rows.append(rec)
        print('[l4] %-28s pycdc(rc=%s,%ss) verify=%s %s/%s' % (
            slug, rec['pycdc']['rc'], rec['pycdc']['elapsed'],
            rec['verify'].get('status'), rec['verify'].get('units_success'),
            rec['verify'].get('units_total')), flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'rows': rows, 'start': args.start, 'count': args.count}, f,
                  ensure_ascii=False, indent=1)
    print('-> %s (%d rows)' % (args.out, len(rows)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
