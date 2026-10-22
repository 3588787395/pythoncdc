#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 执行级语义差分（§3）。

任务要求：「对其中 ≥8 个可安全执行的样例，在隔离临时目录中以同一输入序列跑原模块与产物，
比对返回值/副作用/异常类型」。

本脚本的做法：
  * **两侧各跑一个独立子进程**（原模块 = 原件 .pyc；产物 = offcorpus/<slug>OK.py），
    cwd = 各自的**空隔离临时目录**；
  * 同一份 probe 规格（表达式 / 代码块）按序执行，逐条记录：
      - 返回值的 `repr` 与**类型名**（类型敏感：`1` vs `True` vs `1.0` 不可混同）；
      - 抛出的异常**类型名 + 消息**；
      - 执行期间捕获的 **stdout / stderr**（副作用顺序的可观测面）；
      - 执行后隔离目录里**新增的文件**（文件副作用）；
  * 逐条比对两侧读数，产出 EQUAL / DIFFERENT 判定与差异说明。

用法：
  python -X utf8 l4_semdiff.py --probes exec_probes.json --out logs/l4_semdiff.json
  python -X utf8 l4_semdiff.py --worker <pyc|py> <path> <dotted> <specjson>
"""
from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.machinery
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND6 = os.path.dirname(HERE)
LOGS = os.path.join(ROUND6, 'logs')
OFF = os.path.join(ROUND6, 'offcorpus')

ADDR = re.compile(r'0x[0-9a-fA-F]{6,}')


def norm_text(s: str) -> str:
    return ADDR.sub('0xADDR', s or '')


def load_module(kind: str, path: str, dotted: str):
    """按 .pyc / .py 载入模块，尽量还原包上下文（相对导入）。"""
    parent, _, child = dotted.rpartition('.')
    if parent:
        try:
            importlib.import_module(parent)
        except Exception:
            pass
    if kind == 'pyc':
        loader = importlib.machinery.SourcelessFileLoader(dotted, path)
    else:
        loader = importlib.machinery.SourceFileLoader(dotted, path)
    spec = importlib.util.spec_from_file_location(dotted, path, loader=loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[dotted] = mod
    spec.loader.exec_module(mod)
    if parent:
        try:
            setattr(sys.modules[parent], child, mod)
        except Exception:
            pass
    return mod


def snapshot_files(d):
    out = []
    for dp, _dn, fn in os.walk(d):
        for f in fn:
            p = os.path.join(dp, f)
            try:
                out.append('%s:%d' % (os.path.relpath(p, d), os.path.getsize(p)))
            except OSError:
                pass
    return sorted(out)


def worker(kind, path, dotted, spec_json):
    spec = json.loads(spec_json)
    sandbox = tempfile.mkdtemp(prefix='l4sd_')
    old_cwd = os.getcwd()
    os.chdir(sandbox)
    buf_out, buf_err = io.StringIO(), io.StringIO()
    result = {'kind': kind, 'path': path, 'dotted': dotted, 'import': {}, 'probes': []}
    try:
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            mod = load_module(kind, path, dotted)
        result['import'] = {'ok': True, 'stdout': norm_text(buf_out.getvalue()),
                            'stderr': norm_text(buf_err.getvalue()),
                            'files': snapshot_files(sandbox)}
        pub = []
        for name in sorted(dir(mod)):
            if name.startswith('_'):
                continue
            obj = getattr(mod, name)
            if isinstance(obj, type):
                pub.append('class ' + name)
            elif callable(obj):
                pub.append('def ' + name)
            else:
                pub.append('var ' + name)
        result['public_names'] = pub
    except BaseException as exc:  # noqa: BLE001
        result['import'] = {'ok': False, 'error': '%s: %s' % (type(exc).__name__, exc),
                            'stdout': norm_text(buf_out.getvalue()),
                            'stderr': norm_text(buf_err.getvalue()),
                            'files': snapshot_files(sandbox)}
        result['public_names'] = []
        print(json.dumps(result, ensure_ascii=False, default=str))
        os.chdir(old_cwd)
        shutil.rmtree(sandbox, ignore_errors=True)
        return 0

    for p in spec.get('probes', []):
        rec = {'label': p.get('label', '')}
        bo, be = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(bo), contextlib.redirect_stderr(be):
                if 'expr' in p:
                    val = eval(p['expr'], mod.__dict__)  # noqa: S307 - 隔离进程内、固定规格
                    rec['kind'] = 'return'
                    rec['value'] = norm_text(repr(val))
                    rec['type'] = type(val).__name__
                else:
                    code = p['code']
                    g = dict(mod.__dict__)
                    exec(compile(code, '<probe>', 'exec'), g)  # noqa: S102 - 隔离进程内、固定规格
                    rec['kind'] = 'ok'
                    rec['value'] = None
                    rec['type'] = None
            rec['stdout'] = norm_text(bo.getvalue())
            rec['stderr'] = norm_text(be.getvalue())
        except BaseException as exc:  # noqa: BLE001
            rec['kind'] = 'raise'
            rec['value'] = norm_text('%s: %s' % (type(exc).__name__, exc))
            rec['type'] = type(exc).__name__
            rec['stdout'] = norm_text(bo.getvalue())
            rec['stderr'] = norm_text(be.getvalue())
        rec['files'] = snapshot_files(sandbox)
        result['probes'].append(rec)
    print(json.dumps(result, ensure_ascii=False, default=str))
    os.chdir(old_cwd)
    shutil.rmtree(sandbox, ignore_errors=True)
    return 0


def run_side(kind, path, dotted, spec, timeout=60):
    cmd = [sys.executable, '-X', 'utf8', os.path.abspath(__file__), '--worker', kind, path, dotted,
           json.dumps(spec, ensure_ascii=False)]
    try:
        p = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace',
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return {'kind': 'TIMEOUT', 'import': {'ok': False, 'error': 'timeout'},
                'probes': [], 'public_names': []}
    out = (p.stdout or '').strip().splitlines()
    if not out:
        return {'kind': 'ERROR', 'import': {'ok': False, 'error': (p.stderr or '')[-400:]},
                'probes': [], 'public_names': []}
    try:
        return json.loads(out[-1])
    except ValueError:
        return {'kind': 'ERROR', 'import': {'ok': False, 'error': out[-1][:400]},
                'probes': [], 'public_names': []}


def compare(a, b):
    """两侧读数比对。"""
    diffs = []
    ai, bi = a.get('import', {}), b.get('import', {})
    if ai.get('ok') != bi.get('ok'):
        diffs.append('导入结果不同: 原=%s(%s) 产物=%s(%s)' % (
            ai.get('ok'), (ai.get('error') or '')[:120], bi.get('ok'), (bi.get('error') or '')[:120]))
    elif ai.get('ok'):
        if ai.get('stdout') != bi.get('stdout'):
            diffs.append('导入期 stdout 不同:\n    原: %r\n    产物: %r' % (
                (ai.get('stdout') or '')[:400], (bi.get('stdout') or '')[:400]))
        if ai.get('stderr') != bi.get('stderr'):
            diffs.append('导入期 stderr 不同:\n    原: %r\n    产物: %r' % (
                (ai.get('stderr') or '')[:400], (bi.get('stderr') or '')[:400]))
    ap_, bp_ = a.get('public_names', []), b.get('public_names', [])
    only_a = sorted(set(ap_) - set(bp_))
    only_b = sorted(set(bp_) - set(ap_))
    if only_a:
        diffs.append('仅原模块有: %s' % ', '.join(only_a[:12]))
    if only_b:
        diffs.append('仅产物有: %s' % ', '.join(only_b[:12]))
    n = max(len(a.get('probes', [])), len(b.get('probes', [])))
    rows = []
    for i in range(n):
        pa = a.get('probes', [{}] * n)[i] if i < len(a.get('probes', [])) else {'kind': 'MISSING'}
        pb = b.get('probes', [{}] * n)[i] if i < len(b.get('probes', [])) else {'kind': 'MISSING'}
        same = (pa.get('kind') == pb.get('kind') and pa.get('value') == pb.get('value')
                and pa.get('type') == pb.get('type') and pa.get('stdout') == pb.get('stdout')
                and pa.get('stderr') == pb.get('stderr') and pa.get('files') == pb.get('files'))
        row = {'label': pa.get('label') or pb.get('label') or ('probe#%d' % i),
               'src_kind': pa.get('kind'), 'src_value': pa.get('value'), 'src_type': pa.get('type'),
               'src_stdout': pa.get('stdout'),
               'prod_kind': pb.get('kind'), 'prod_value': pb.get('value'), 'prod_type': pb.get('type'),
               'prod_stdout': pb.get('stdout'),
               'equal': bool(same)}
        if not same:
            if pa.get('kind') != pb.get('kind'):
                row['reason'] = '行为类别不同: 原=%s 产物=%s' % (pa.get('kind'), pb.get('kind'))
            elif pa.get('value') != pb.get('value') or pa.get('type') != pb.get('type'):
                row['reason'] = '返回值/类型不同: 原=%s(%s) 产物=%s(%s)' % (
                    pa.get('value'), pa.get('type'), pb.get('value'), pb.get('type'))
            elif pa.get('stdout') != pb.get('stdout'):
                row['reason'] = 'stdout（副作用序）不同: 原=%r 产物=%r' % (
                    (pa.get('stdout') or '')[:200], (pb.get('stdout') or '')[:200])
            elif pa.get('stderr') != pb.get('stderr'):
                row['reason'] = 'stderr 不同'
            else:
                row['reason'] = '文件副作用不同: 原=%s 产物=%s' % (pa.get('files'), pb.get('files'))
        rows.append(row)
    return diffs, rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--worker', nargs=4, metavar=('KIND', 'PATH', 'DOTTED', 'SPEC'))
    ap.add_argument('--probes', required=False, default=os.path.join(ROUND6, 'exec_probes.json'))
    ap.add_argument('--out', default=os.path.join(LOGS, 'l4_semdiff.json'))
    ap.add_argument('--only', nargs='*', default=None)
    ap.add_argument('--timeout', type=int, default=60)
    args = ap.parse_args()
    if args.worker:
        return worker(*args.worker)
    probes = json.load(open(args.probes, encoding='utf-8'))['samples']
    if args.only:
        probes = [p for p in probes if p['slug'] in args.only]
    rows = []
    for p in probes:
        slug = p['slug']
        orig_pyc = p['pyc']
        prod = os.path.join(OFF, slug + 'OK.py')
        dotted = p['dotted']
        spec = {'probes': p['probes']}
        a = run_side('pyc', orig_pyc, dotted, spec, args.timeout)
        b = run_side('py', prod, dotted, spec, args.timeout)
        diffs, prows = compare(a, b)
        rec = {'slug': slug, 'dotted': dotted, 'pyc': orig_pyc, 'product': prod,
               'orig_import': a.get('import'), 'prod_import': b.get('import'),
               'n_probes': len(prows), 'n_diff': sum(1 for r in prows if not r['equal']),
               'module_diffs': diffs, 'probes': prows,
               'src_public': a.get('public_names', []), 'prod_public': b.get('public_names', [])}
        rows.append(rec)
        print('[semdiff] %-28s probes=%d diff=%d modulediffs=%d' % (
            slug, len(prows), rec['n_diff'], len(diffs)))
        for d in diffs:
            print('    MODULE: %s' % d.replace('\n', ' ')[:200])
        for r in prows:
            if not r['equal']:
                print('    DIFF  %-34s %s' % (r['label'], r.get('reason', '')[:160]))
    with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'rows': rows}, f, ensure_ascii=False, indent=1)
    tot = sum(r['n_probes'] for r in rows)
    df = sum(r['n_diff'] for r in rows)
    print('-> samples=%d probes=%d diff=%d' % (len(rows), tot, df))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
