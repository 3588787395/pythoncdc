#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 真实模块的**最小化复现**（delta debugging）。

通用小样例无法复现语料外缺陷（见 logs/l4_repro.json：10 个通用样例 9 个「不复现」），
说明缺陷是**上下文相关**的。因此这里对**真实模块源码**做最小化：
逐个删除顶层 def/class 块，只要「同一缺陷签名」仍然存在就保留删除。

缺陷签名（predicate）：
  * 源侧执行成功（rc == 0）；
  * 产物侧与源侧 stdout 不同，且产物侧是**抛异常**或 stdout 缺关键内容。

输出：repro/min_<slug>.py（最小化后的真实源码）+ logs/l4_minimize.json
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import py_compile
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND6 = os.path.dirname(HERE)
LOGS = os.path.join(ROUND6, 'logs')
REPRO = os.path.join(ROUND6, 'repro')
REPO = os.path.abspath(os.path.join(ROUND6, '..', '..', '..', '..', '..'))

RUNNER = (
    "import importlib.util, sys\n"
    "spec = importlib.util.spec_from_file_location('m', sys.argv[1])\n"
    "m = importlib.util.module_from_spec(spec)\n"
    "sys.modules['m'] = m\n"
    "spec.loader.exec_module(m)\n"
    "m.main()\n"
)


def top_level_blocks(src: str):
    """顶层 def/class 块 -> (name, start_line, end_line)（1-based, 闭区间）。"""
    tree = ast.parse(src)
    lines = src.splitlines(True)
    out = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = min([d.lineno for d in node.decorator_list] + [node.lineno])
            out.append((node.name, start, node.end_lineno))
    out.sort(key=lambda x: -(x[2] - x[1]))
    return out


def remove_block(src: str, start: int, end: int) -> str:
    lines = src.splitlines(True)
    return ''.join(lines[:start - 1] + lines[end:])


def compile_and_decompile(src_text: str, workdir: str, tag: str):
    py = os.path.join(workdir, tag + '.py')
    pyc = os.path.join(workdir, tag + '.pyc')
    prod = os.path.join(workdir, tag + 'OK.py')
    with open(py, 'w', encoding='utf-8', newline='\n') as f:
        f.write(src_text)
    try:
        py_compile.compile(py, cfile=pyc, doraise=True)
    except Exception:
        return None, None
    if os.path.exists(prod):
        os.remove(prod)
    try:
        subprocess.run([sys.executable, '-X', 'utf8', 'pycdc.py', pyc, '-o', prod],
                       capture_output=True, timeout=120, cwd=REPO)
    except subprocess.TimeoutExpired:
        return py, None
    return py, (prod if os.path.exists(prod) else None)


def run_main(path: str, timeout=25):
    try:
        p = subprocess.run([sys.executable, '-X', 'utf8', '-c', RUNNER, path],
                           capture_output=True, text=True, encoding='utf-8',
                           errors='replace', timeout=timeout, cwd=REPO)
        return {'rc': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except subprocess.TimeoutExpired:
        return {'rc': None, 'stdout': '', 'stderr': 'TIMEOUT'}


def defect_signature(src_run, prod_run):
    """返回缺陷签名（字符串）或 None。"""
    if src_run['rc'] != 0:
        return None
    if prod_run['rc'] == 0 and src_run['stdout'] == prod_run['stdout']:
        return None
    if prod_run['rc'] != 0:
        err = (prod_run['stderr'] or '').strip().splitlines()
        last = err[-1][:160] if err else 'rc=%s' % prod_run['rc']
        return 'raise:' + last
    return 'stdout-diff'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--slug', required=True)
    ap.add_argument('--module', required=True, help='真实模块源码路径')
    ap.add_argument('--probe', required=True, help='追加到模块末尾的 main() 探针源码')
    ap.add_argument('--max-seconds', type=int, default=200)
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    t0 = time.time()
    src = open(args.module, encoding='utf-8').read()
    if os.path.exists(args.probe):
        probe_src = open(args.probe, encoding='utf-8').read()
    else:
        probe_src = args.probe
    base = src + '\n\n' + probe_src + '\n'
    work = os.path.join(REPRO, 'min_work_' + args.slug)
    os.makedirs(work, exist_ok=True)

    py, prod = compile_and_decompile(base, work, 'cand')
    if prod is None:
        print('[min] %s: 初始产物生成失败' % args.slug)
        return 1
    sig = defect_signature(run_main(py), run_main(prod))
    print('[min] %s: 初始缺陷签名 = %s' % (args.slug, sig))
    if sig is None:
        print('[min] %s: 初始状态无缺陷，无法最小化' % args.slug)
        return 1

    cur = base
    removed = []
    while time.time() - t0 < args.max_seconds:
        blocks = top_level_blocks(cur)
        progressed = False
        for name, s, e in blocks:
            if time.time() - t0 > args.max_seconds:
                break
            cand = remove_block(cur, s, e)
            if not cand.strip():
                continue
            py2, prod2 = compile_and_decompile(cand, work, 'cand')
            if prod2 is None:
                continue
            sig2 = defect_signature(run_main(py2), run_main(prod2))
            if sig2 == sig:
                cur = cand
                removed.append(name)
                progressed = True
                print('[min] %s: 删除块 %-28s 仍复现（已删 %d）' % (args.slug, name, len(removed)))
                break
        if not progressed:
            break

    outp = args.out or os.path.join(REPRO, 'min_%s.py' % args.slug)
    with open(outp, 'w', encoding='utf-8', newline='\n') as f:
        f.write(cur)
    pyc = os.path.join(REPRO, 'min_%s.pyc' % args.slug)
    try:
        py_compile.compile(outp, cfile=pyc, doraise=True)
    except Exception:
        pass
    rec = {'slug': args.slug, 'module': args.module, 'reduced_file': outp,
           'removed_blocks': removed, 'signature': sig,
           'orig_lines': len(base.splitlines()), 'reduced_lines': len(cur.splitlines()),
           'elapsed': round(time.time() - t0, 1)}
    with open(os.path.join(LOGS, 'l4_minimize.json'), 'a', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print('[min] %s: %d 行 -> %d 行，删除块 %d 个，用时 %.1fs -> %s' % (
        args.slug, rec['orig_lines'], rec['reduced_lines'], len(removed), rec['elapsed'], outp))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
