#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — B142 / B143 在**语料外**真实代码上的复现复核（§5）。

B142（前规范登记）：嵌套 try/finally 内的 `continue` —— analyzer 把「正常路径 finally
     副本」误纳入外层 try 体 ⇒ continue 形态整条丢失 + finally 体互换重复。
B143（前规范登记）：`finally` 体内的 `break` —— finalbody 装配线性发射 ⇒ break 落错块。

做法：
  1. 用 AST 在**语料外真实源码**里搜这两种形态（continue in try-with-finally；
     break in try.finalbody）；
  2. 命中模块 → 编译 → pycdc → pyc_verify；
  3. **源码 vs 产物**结构比对：Try / finalbody / Continue / Break 的**出现次数**
     与所在嵌套深度（B142 的症状 = finally 副本重复 ⇒ Try 计数膨胀；
     B143 的症状 = break 落到 finalbody 之外 ⇒ Break 计数/位置变化）。

输出：logs/l4_b142_b143.json
"""
from __future__ import annotations

import ast
import glob
import json
import os
import py_compile
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND6 = os.path.dirname(HERE)
LOGS = os.path.join(ROUND6, 'logs')
WORK = os.path.join(ROUND6, 'b142b143')
REPO = os.path.abspath(os.path.join(ROUND6, '..', '..', '..', '..', '..'))

ROOTS = [r'D:\Python\Lib', r'D:\Python\Lib\site-packages',
         os.path.join(REPO, 'core'), os.path.join(REPO, 'parsers'),
         os.path.join(REPO, 'tools'), os.path.join(REPO, 'scripts')]


def in_loop(node, stop):
    for p in ast.walk(node):
        if p is stop:
            continue
    return True


def scan_file(path):
    """返回该文件中的 B142 / B143 命中（函数名 + 行号 + 形态）。"""
    try:
        if os.path.getsize(path) > 3_000_000:
            return []
        src = open(path, encoding='utf-8', errors='replace').read()
    except OSError:
        return []
    # 快速文本预筛：必须同时含 finally 与 continue/break
    if 'finally' not in src or ('continue' not in src and 'break' not in src):
        return []
    try:
        tree = ast.parse(src)
    except Exception:
        return []
    hits = []

    def walk_func(fn, parents):
        for node in ast.walk(fn):
            if not isinstance(node, ast.Try):
                continue
            # B142: try 带 finally，且其内部（含嵌套）有 continue
            if node.finalbody:
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Continue):
                        hits.append({'kind': 'B142', 'func': fn.name, 'line': sub.lineno,
                                     'try_line': node.lineno,
                                     'nested_try': any(isinstance(p, ast.Try) for p in parents),
                                     'detail': 'continue@%d 处于 try(finalbody@%d) 内' % (
                                         sub.lineno, node.lineno)})
                        break
            # B143: break 出现在 finally 体里
            for st in node.finalbody:
                for sub in ast.walk(st):
                    if isinstance(sub, ast.Break):
                        hits.append({'kind': 'B143', 'func': fn.name, 'line': sub.lineno,
                                     'try_line': node.lineno, 'nested_try': False,
                                     'detail': 'break@%d 处于 finalbody@%d 内' % (sub.lineno, node.lineno)})
                        break
        for child in ast.iter_child_nodes(fn):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                walk_func(child, parents + [node])

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            walk_func(node, [])
    return hits


def counts(tree, name):
    """指定函数在 AST 中的结构计数。"""
    out = {}

    def visit(fn):
        c = {'Try': 0, 'finalbody': 0, 'Continue': 0, 'Break': 0, 'handlers': 0}
        for node in ast.walk(fn):
            if isinstance(node, ast.Try):
                c['Try'] += 1
                c['finalbody'] += len(node.finalbody)
                c['handlers'] += len(node.handlers)
            elif isinstance(node, ast.Continue):
                c['Continue'] += 1
            elif isinstance(node, ast.Break):
                c['Break'] += 1
        return c

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            out.setdefault(name, []).append(visit(node))
    return out


def run(cmd, timeout=150, cwd=REPO):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                           errors='replace', timeout=timeout, cwd=cwd)
        return {'rc': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except subprocess.TimeoutExpired:
        return {'rc': None, 'stdout': '', 'stderr': 'TIMEOUT'}


def main() -> int:
    os.makedirs(WORK, exist_ok=True)
    # 1) 扫描
    files = []
    for root in ROOTS:
        for dp, dn, fn in os.walk(root):
            if '__pycache__' in dp or 'node_modules' in dp:
                continue
            for f in fn:
                if f.endswith('.py'):
                    files.append(os.path.join(dp, f))
    print('[scan] %d 个候选文件' % len(files))
    hits_by_file = {}
    for i, p in enumerate(files):
        for h in scan_file(p):
            hits_by_file.setdefault(p, []).append(h)
    b142 = {p: [h for h in hs if h['kind'] == 'B142'] for p, hs in hits_by_file.items()}
    b143 = {p: [h for h in hs if h['kind'] == 'B143'] for p, hs in hits_by_file.items()}
    b142 = {p: v for p, v in b142.items() if v}
    b143 = {p: v for p, v in b143.items() if v}
    print('[scan] B142 命中文件 %d；B143 命中文件 %d' % (len(b142), len(b143)))
    with open(os.path.join(LOGS, 'l4_b142_b143_scan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'n_files': len(files), 'b142': b142, 'b143': b143},
                  f, ensure_ascii=False, indent=1)

    # 2) 取样复现（每个形态最多 6 个模块）
    results = []
    for kind, pool in (('B142', b142), ('B143', b143)):
        for path, hits in sorted(pool.items(), key=lambda kv: -len(kv[1]))[:6]:
            slug = '%s_%s' % (kind.lower(), os.path.splitext(os.path.basename(path))[0])
            pyc = os.path.join(WORK, slug + '.pyc')
            prod = os.path.join(WORK, slug + 'OK.py')
            rec = {'kind': kind, 'module': path, 'hits': hits, 'slug': slug}
            try:
                py_compile.compile(path, cfile=pyc, doraise=True)
            except Exception as exc:
                rec['error'] = 'compile: %s' % str(exc)[:120]
                results.append(rec)
                continue
            d = run([sys.executable, '-X', 'utf8', 'pycdc.py', pyc, '-o', prod])
            rec['pycdc'] = {'rc': d['rc']}
            if not os.path.exists(prod):
                rec['error'] = '无产物'
                results.append(rec)
                print('[%s] %-46s 无产物' % (kind, os.path.basename(path)))
                continue
            v = run([sys.executable, '-X', 'utf8', 'scripts/pyc_verify.py', 'single', pyc,
                     '--source', prod])
            status = None
            for line in (v['stdout'] or '').splitlines():
                if line.strip().startswith('[single] status='):
                    for part in line.split():
                        if part.startswith('status='):
                            status = part.split('=', 1)[1]
            rec['verify_status'] = status
            try:
                st = ast.parse(open(path, encoding='utf-8', errors='replace').read())
                pt = ast.parse(open(prod, encoding='utf-8', errors='replace').read())
            except Exception as exc:
                rec['error'] = 'parse: %s' % str(exc)[:120]
                results.append(rec)
                continue
            per = []
            for h in hits:
                sc = counts(st, h['func'])
                pc = counts(pt, h['func'])
                per.append({'func': h['func'], 'line': h['line'], 'detail': h['detail'],
                            'src': sc.get(h['func']), 'prod': pc.get(h['func'])})
            rec['compare'] = per
            repro = False
            for a in per:
                s1 = (a.get('src') or [None])[0]
                p1 = (a.get('prod') or [None])[0]
                if not s1 or not p1:
                    continue
                if (s1['Try'] != p1['Try'] or s1['finalbody'] != p1['finalbody']
                        or s1['Continue'] != p1['Continue'] or s1['Break'] != p1['Break']):
                    repro = True
            rec['reproduced'] = repro
            results.append(rec)
            print('[%s] %-46s verify=%-10s reproduced=%s' % (
                kind, os.path.basename(path), status, rec.get('reproduced')))
    with open(os.path.join(LOGS, 'l4_b142_b143.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'results': results}, f, ensure_ascii=False, indent=1)
    n142 = sum(1 for r in results if r['kind'] == 'B142' and r.get('reproduced'))
    n143 = sum(1 for r in results if r['kind'] == 'B143' and r.get('reproduced'))
    print('=> B142 复现 %d / B143 复现 %d' % (n142, n143))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
