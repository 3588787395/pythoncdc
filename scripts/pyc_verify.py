#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""唯一的反编译验证判据。

判据本身不在这里实现：本文件只做装载、配对与报告，逐条判定由附件 pylingual 的
`pylingual/equivalence_check.py::compare_pyc` 执行（默认根目录
`D:/Desktop/ptrade相关/pylingual`，可用 --pylingual 改）。报告头部写下该文件的
sha256，读数因此可追溯到具体字节。

compare_pyc 对每个 code object（含嵌套，前缀命名）产出一条 TestResult：
  Missing bytecode / Extra bytecode / Different control flow / Different bytecode / Equal
一个文件全部 Equal 才算 success（pylingual dev_scripts/cflow.py:86 的判定）；
成功率 = 相等单元数 / 单元总数（pylingual DecompilerResult.calculate_success_rate）。

两个仅为"能导入"而存在的垫片，不改变任何判定：
  typing.override —— pylingual 用了 3.12 才有的标准库符号，运行时语义就是恒等装饰器；
  pydot          —— 只在 pylingual/control_flow_reconstruction/cfg.py 画 CFG 时用到，
                     compare_pyc 路径上不会调用（那里 iterate=False，不 visualize）。

用法：
  python scripts/pyc_verify.py single <a.pyc> [--source <x.py>]
  python scripts/pyc_verify.py batch --index pyc_index.json --json verify/report.json
  python scripts/pyc_verify.py compare --before old.json --after new.json
  python scripts/pyc_verify.py selfcheck <a.pyc>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import py_compile
import re
import shutil
import sys
import tempfile
import time
import types

DEFAULT_PYLINGUAL = r'D:\Desktop\ptrade相关\pylingual'
CATEGORIES = ('success', 'failure', 'compile_error', 'error')


# ─── 装载附件判据 ───────────────────────────────────────────────────────────


def load_compare_pyc(root: str):
    root = os.path.abspath(root)
    if not os.path.isfile(os.path.join(root, 'pylingual', 'equivalence_check.py')):
        sys.exit('[fatal] 找不到 pylingual 判据：%s\\pylingual\\equivalence_check.py\n'
                 '        用 --pylingual 指定正确的仓库根目录；本工具不提供任何备用判据。' % root)
    sys.path.insert(0, root)

    import typing
    if not hasattr(typing, 'override'):          # 3.11 缺 3.12 的符号；运行时语义为恒等
        typing.override = lambda func: func
    if 'pydot' not in sys.modules:               # 只被 pylingual 的画图函数使用
        stub = types.ModuleType('pydot')
        stub.graph_from_dot_data = lambda *a, **k: []
        stub.Dot = stub.Node = stub.Edge = lambda *a, **k: None
        sys.modules['pydot'] = stub
    if 'pylingual' not in sys.modules:           # 绕开 __init__.py（会拉起整套 ML 反编译器）
        pkg = types.ModuleType('pylingual')
        pkg.__path__ = [os.path.join(root, 'pylingual')]
        sys.modules['pylingual'] = pkg

    from pylingual.equivalence_check import compare_pyc
    return compare_pyc


def sha256(path: str, n: int = 64) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()[:n]


def ruler_stamp(root: str) -> dict:
    eq = os.path.join(os.path.abspath(root), 'pylingual', 'equivalence_check.py')
    return {'compare_pyc': eq.replace('\\', '/'),
            'compare_pyc_sha256': sha256(eq, 16),
            'ruler_version': 'pylingual-equivalence_check'}


# ─── 单个 pyc 的判定 ────────────────────────────────────────────────────────


def product_of(pyc: str) -> str | None:
    return pyc[:-4] + 'OK.py' if pyc.lower().endswith('.pyc') else None


def evaluate(pyc: str, source: str, tmpdir: str, compare_pyc) -> dict:
    """跑一次 compare_pyc：逐单元 verdict + 文件级桶 + 单元计数。"""
    row = {'pyc': pyc.replace('\\', '/'), 'source': source.replace('\\', '/'),
           'pyc_sha': sha256(pyc, 12), 'source_sha': sha256(source, 12),
           'status': None, 'units_total': 0, 'units_success': 0,
           'success_rate': None, 'failures': [], 'detail': None}
    recompiled = os.path.join(tmpdir, os.path.basename(pyc))
    try:
        py_compile.compile(source, cfile=recompiled, doraise=True, optimize=0)
    except py_compile.PyCompileError as exc:
        row['status'] = 'compile_error'
        row['detail'] = str(exc).strip()[:400]
        return row
    except (SyntaxError, ValueError, OSError) as exc:
        row['status'] = 'compile_error'
        row['detail'] = '%s: %s' % (type(exc).__name__, exc)
        return row

    try:
        results = compare_pyc(pyc, recompiled)
    except Exception as exc:
        row['status'] = 'error'
        row['detail'] = '%s: %s' % (type(exc).__name__, exc)
        row['failures'] = [row['detail']]
        return row
    finally:
        if os.path.isfile(recompiled):
            os.remove(recompiled)

    row['units_total'] = len(results)
    row['units_success'] = sum(1 for r in results if r.success)
    if not results:
        row['status'] = 'error'
        row['detail'] = 'compare_pyc 未产出任何单元（读数无效）'
        return row
    row['success_rate'] = row['units_success'] / row['units_total']
    row['status'] = 'success' if row['units_success'] == row['units_total'] else 'failure'
    row['failures'] = [str(r) for r in results if not r.success]
    return row


# ─── 目标清单 ───────────────────────────────────────────────────────────────


def collect_targets(args) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    if args.index:
        with open(args.index, encoding='utf-8') as f:
            entries = json.load(f)
        for e in entries:
            pairs.append((e['path'].replace('/', os.sep), e.get('source')))
    for extra in getattr(args, 'pyc', []):
        pairs.append((os.path.abspath(extra), None))
    out = []
    for pyc, src in pairs:
        if not os.path.isfile(pyc):
            sys.exit('[fatal] pyc 不存在：%s' % pyc)
        src = src or product_of(pyc)
        if not src or not os.path.isfile(src):
            sys.exit('[fatal] 缺少反编译产物：%s（期望 %sOK.py）' % (pyc, pyc[:-4]))
        out.append((pyc, src))
    if getattr(args, 'limit', None):
        out = out[:args.limit]
    return out


# ─── 子命令 ─────────────────────────────────────────────────────────────────


def cmd_single(args, compare_pyc) -> int:
    pyc = os.path.abspath(args.pyc)
    source = os.path.abspath(args.source or product_of(pyc))
    if not os.path.isfile(source):
        sys.exit('[fatal] 缺少产物 %s' % source)
    tmp = tempfile.mkdtemp(prefix='pycverify_')
    try:
        row = evaluate(pyc, source, tmp, compare_pyc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for line in row['failures']:
        print('  ' + line)
    print('[single] %s' % row['pyc'])
    print('[single] 产物 %s' % row['source'])
    print('[single] status=%s units=%d/%d success_rate=%s' % (
        row['status'], row['units_success'], row['units_total'],
        '-' if row['success_rate'] is None else '%.2f%%' % (100 * row['success_rate'])))
    return 0 if row['status'] == 'success' else 1


def cmd_batch(args, compare_pyc) -> int:
    targets = collect_targets(args)
    t0 = time.time()
    rows = []
    tmp = tempfile.mkdtemp(prefix='pycverify_batch_')
    try:
        for i, (pyc, src) in enumerate(targets, 1):
            rows.append(evaluate(pyc, src, tmp, compare_pyc))
            r = rows[-1]
            if args.verbose or len(targets) <= 20:
                print('[%d/%d] %-9s %3d/%-3d %s' % (i, len(targets), r['status'],
                                                     r['units_success'], r['units_total'],
                                                     r['pyc'].split('site-packages/')[-1]), flush=True)
            elif i % 25 == 0:
                print('... %d/%d  %.0fs  units=%d/%d' % (
                    i, len(targets), time.time() - t0, r['units_success'], r['units_total']), flush=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    units_total = sum(r['units_total'] for r in rows)
    units_ok = sum(r['units_success'] for r in rows)
    buckets = {c: sorted(r['pyc'] for r in rows if r['status'] == c) for c in CATEGORIES}
    report = {'generated_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
              'elapsed_sec': round(time.time() - t0, 1),
              'interpreter': sys.version.split()[0],
              'ruler': ruler_stamp(args.pylingual),
              'files_total': len(rows),
              'units_total': units_total,
              'units_success': units_ok,
              'success_rate': (units_ok / units_total) if units_total else None,
              'files_by_status': {c: len(v) for c, v in buckets.items()},
              'paths_by_status': buckets,
              'rows': rows}
    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True) + '\n')
    print(json.dumps({'ruler': report['ruler'], 'interpreter': report['interpreter'],
                      'files_total': report['files_total'], 'units_total': units_total,
                      'units_success': units_ok, 'success_rate': report['success_rate'],
                      'files_by_status': report['files_by_status'],
                      'elapsed_sec': report['elapsed_sec']}, ensure_ascii=False, indent=1))
    if args.json:
        print('-> %s' % args.json)
    if not units_total:
        sys.exit('[fatal] 没有任何单元，读数无效')
    return 1 if buckets['error'] or buckets['compile_error'] else 0


def cmd_compare(args, _compare_pyc) -> int:
    """Movement Matrix（形状取自 pylingual dev_scripts/evaluate_cflow.py:175-284）。"""
    before = json.load(open(args.before, encoding='utf-8'))
    after = json.load(open(args.after, encoding='utf-8'))
    cat_a = {p: c for c, ps in before['paths_by_status'].items() for p in ps}
    cat_b = {p: c for c, ps in after['paths_by_status'].items() for p in ps}
    paths = set(cat_a) | set(cat_b)
    matrix = {a: {b: 0 for b in CATEGORIES} for a in CATEGORIES}
    moved = {a: {b: [] for b in CATEGORIES} for a in CATEGORIES}
    for p in sorted(paths):
        a, b = cat_a.get(p), cat_b.get(p)
        if a and b:
            matrix[a][b] += 1
            if a != b:
                moved[a][b].append(p)

    print('Movement Matrix (before -> after)')
    print(' ' * 16 + ''.join('%-14s' % b for b in CATEGORIES))
    for a in CATEGORIES:
        print('%-16s' % a + ''.join('%-14s' % ('-' if not matrix[a][b] else
                                               (str(matrix[a][b]) if a == b else
                                                '+%d' % matrix[a][b])) for b in CATEGORIES))
    for a in CATEGORIES:
        for b in CATEGORIES:
            if a != b and moved[a][b]:
                print('\n%s -> %s (%d)' % (a, b, len(moved[a][b])))
                for p in moved[a][b]:
                    print('- ' + p)
    new = sorted(p for p in paths if p not in cat_a)
    gone = sorted(p for p in paths if p not in cat_b)
    if new:
        print('\nNew (%d)' % len(new))
        for p in new:
            print('- %s (added as %s)' % (p, cat_b[p]))
    if gone:
        print('\nRemoved (%d)' % len(gone))
        for p in gone:
            print('- %s (was %s)' % (p, cat_a[p]))

    da, db = before['units_success'], after['units_success']
    ta, tb = before['units_total'], after['units_total']
    print('\nunits: %d/%d (%.2f%%) -> %d/%d (%.2f%%)' % (
        da, ta, 100.0 * da / ta, db, tb, 100.0 * db / tb))
    print('files: success %d -> %d' % (before['files_by_status']['success'],
                                        after['files_by_status']['success']))
    regressed = sum(len(moved['success'][b]) for b in CATEGORIES if b != 'success')
    improved = sum(len(moved[a]['success']) for a in CATEGORIES if a != 'success')
    print('REGRESSIONS=%d IMPROVED=%d' % (regressed, improved))
    return 1 if regressed else 0


def cmd_selfcheck(args, compare_pyc) -> int:
    """尺子自检：同一 pyc 自比必须全等；改动产物源码必须被抓出来。"""
    pyc = os.path.abspath(args.pyc)
    source = os.path.abspath(args.source or product_of(pyc))
    src = open(source, encoding='utf-8').read()
    tmp = tempfile.mkdtemp(prefix='pycverify_sc_')
    fails = []
    try:
        same = compare_pyc(pyc, _compile(src, tmp, 'same.pyc'))
        bad = [r for r in same if not r.success]
        print('[selfcheck] 自证：%d/%d 单元 Equal' % (len(same) - len(bad), len(same)))
        if not same or bad:
            fails.append('自证失败：%s 与自身判为 %d 个缺陷' % (os.path.basename(pyc), len(bad)))
        for name, mutated in (('常量', _mutate_return(src)), ('极性', _mutate_compare(src))):
            if mutated is None:
                print('[selfcheck] 变异「%s」在本产物里无处可施' % name)
                fails.append('自检不完备：变异「%s」无处可施' % name)
                continue
            try:
                res = compare_pyc(pyc, _compile(mutated, tmp, 'mut.pyc'))
            except py_compile.PyCompileError as exc:
                print('[selfcheck] 变异「%s」编译不过：%s' % (name, str(exc)[:120]))
                fails.append('自检不完备：变异「%s」编译不过' % name)
                continue
            hits = [r for r in res if not r.success]
            print('[selfcheck] 变异「%s」抓到 %d/%d 单元' % (name, len(hits), len(res)))
            if not hits:
                fails.append('判据失灵：变异「%s」未被任何单元抓到' % name)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if fails:
        print('[selfcheck] FAILED:')
        for f in fails:
            print('   - ' + f)
        return 1
    print('[selfcheck] OK —— 判据可用')
    return 0


def _compile(text: str, tmp: str, name: str) -> str:
    src = os.path.join(tmp, name[:-4] + '.py')
    out = os.path.join(tmp, name)
    with open(src, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    py_compile.compile(src, cfile=out, doraise=True, optimize=0)
    return out


def _mutate_return(src: str) -> str | None:
    m = re.search(r'^\s*return (None|True|False|\d+)\s*$', src, re.M)
    if not m:
        return None
    flipped = {'None': '0', 'True': 'False', 'False': 'True'}.get(m.group(1), '7')
    return src[:m.start(1)] + flipped + src[m.end(1):]


def _mutate_compare(src: str) -> str | None:
    for pat, rep in ((r'\bif ([^:\n]+) > ', r'if \1 < '), (r'\bif ([^:\n]+) < ', r'if \1 > '),
                     (r'\bif ([^:\n]+) == ', r'if \1 != '), (r'\bif ([^:\n]+) != ', r'if \1 == ')):
        new, n = re.subn(pat, rep, src, count=1)
        if n:
            return new
    return None


# ─── 入口 ───────────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='唯一判据：附件 pylingual 的 compare_pyc')
    ap.add_argument('--pylingual', default=DEFAULT_PYLINGUAL, help='附件 pylingual 仓库根目录')
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('single', help='验证一个 pyc（默认用同名 OK.py 产物）')
    p.add_argument('pyc')
    p.add_argument('--source')
    p.set_defaults(func=cmd_single)

    p = sub.add_parser('batch', help='按索引或清单批量验证，产出唯一报告')
    p.add_argument('pyc', nargs='*', help='额外的 pyc 路径')
    p.add_argument('--index', help='pyc_index.json：读取每条 entry 的 path')
    p.add_argument('--json', help='把完整报告写到此文件')
    p.add_argument('--limit', type=int)
    p.add_argument('-v', '--verbose', action='store_true')
    p.set_defaults(func=cmd_batch)

    p = sub.add_parser('compare', help='两份 batch 报告之间的 Movement Matrix')
    p.add_argument('--before', required=True)
    p.add_argument('--after', required=True)
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser('selfcheck', help='尺子自检：自比全等 + 变异必抓')
    p.add_argument('pyc')
    p.add_argument('--source')
    p.set_defaults(func=cmd_selfcheck)

    args = ap.parse_args(argv)
    if sys.version_info[:2] != (3, 11):
        sys.exit('[fatal] 语料是 3.11 字节码，必须用 3.11 解释器跑判据（当前 %d.%d）'
                 % sys.version_info[:2])
    compare_pyc = load_compare_pyc(args.pylingual)
    return args.func(args, compare_pyc)


if __name__ == '__main__':
    sys.exit(main())
