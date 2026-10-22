#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 规模与深度边界攻击（§4）。

边界样例（每类 ≥3 个，含**悬崖搜索**：逐级加深度直到失败）：
  * 嵌套深度：括号表达式 / 嵌套调用 / 下标链 / `if` 缩进嵌套
    （注：CPython 词法器的缩进层级上限 ~99 ⇒ 源码本身可能先编译失败，
      该读数单列，不计入 pycdc 的失败）；
  * 函数语句数：520 / 1000 / 2000 条语句；
  * 巨型表达式：5000 项加法链 / 5000 项布尔链 / 巨型字符串拼接。

每个样例的读数：
  pycdc  rc / 耗时 / 是否超时 / 产物大小；
  产物是否可编译（pyc_verify status）；
  **AST 深度与语句数保真度**（源 vs 产物）；
  **执行级结果比对**（源 vs 产物）。

输出：logs/l4_boundary.json + boundary/*.py
"""
from __future__ import annotations

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
BOUND = os.path.join(ROUND6, 'boundary')
REPO = os.path.abspath(os.path.join(ROUND6, '..', '..', '..', '..', '..'))

RUNNER = (
    "import importlib.util, sys\n"
    "spec = importlib.util.spec_from_file_location('m', sys.argv[1])\n"
    "m = importlib.util.module_from_spec(spec)\n"
    "sys.modules['m'] = m\n"
    "spec.loader.exec_module(m)\n"
    "m.main()\n"
)


def gen_nested_paren(depth):
    return ('def main():\n    x = ' + '(' * depth + '1' + ')' * depth + '\n    print(x)\n')


def gen_nested_call(depth):
    body = 'v'
    for i in range(depth):
        body = 'id%d(%s)' % (i, body)
    return ('def id0(v):\n    return v\n\n\n' +
            ''.join('def id%d(v):\n    return id%d(v)\n\n\n' % (i, i - 1) for i in range(1, depth + 1)) +
            'def main():\n    print(%s)\n' % body)


def gen_nested_subscript(depth):
    expr = 'a'
    for i in range(depth):
        expr = '%s[%d]' % (expr, i)
    return ('def main():\n    a = list(range(300))\n    print(%s)\n' % expr)


def gen_nested_if(depth):
    lines = ['def main():', '    x = 0']
    pad = '    '
    for i in range(depth):
        lines.append('%sif x >= 0:' % (pad + '    ' * i))
    lines.append('%sx = 1' % (pad + '    ' * (depth + 1)))
    lines.append('%sprint(x)' % pad)
    return '\n'.join(lines) + '\n'


def gen_nested_if_var(depth):
    """每层**不同的副作用**：若被塌陷成 and 链，语义必错。"""
    lines = ['def main():', '    x = 0']
    pad = '    '
    for i in range(depth):
        lines.append('%sif x >= 0:' % (pad + '    ' * i))
    lines.append('%sx += %d' % (pad + '    ' * (depth + 1), depth))
    lines.append('%sprint(x)' % pad)
    return '\n'.join(lines) + '\n'


def gen_giant_list(n):
    return ('def main():\n    x = [' + ', '.join(str(i) for i in range(n)) +
            ']\n    print(len(x), x[-1])\n')


def gen_stmts(n):
    lines = ['def main():', '    x = 0']
    for i in range(n):
        lines.append('    x += %d' % i)
    lines.append('    print(x)')
    return '\n'.join(lines) + '\n'


def gen_giant_add(n):
    return ('def main():\n    x = ' + ' + '.join(str(i) for i in range(n)) +
            '\n    print(x)\n')


def gen_giant_bool(n):
    return ('def main():\n    x = ' + ' and '.join(['True'] * n) +
            '\n    print(x)\n')


def gen_giant_str(n):
    return ('def main():\n    x = ' + ' + '.join(["'a'"] * n) +
            '\n    print(len(x))\n')


def ast_depth(node):
    best = 0
    stack = [(node, 1)]
    while stack:
        cur, d = stack.pop()
        if d > best:
            best = d
        for ch in ast.iter_child_nodes(cur):
            stack.append((ch, d + 1))
    return best


def ast_stmts(node):
    return sum(1 for _ in ast.walk(node) if isinstance(_, ast.stmt))


def run(cmd, timeout=150, cwd=REPO):
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                           errors='replace', timeout=timeout, cwd=cwd)
        return {'rc': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr,
                'elapsed': round(time.time() - t0, 2), 'timeout': False}
    except subprocess.TimeoutExpired as exc:
        return {'rc': None, 'stdout': (exc.stdout or '') if isinstance(exc.stdout, str) else '',
                'stderr': 'TIMEOUT', 'elapsed': round(time.time() - t0, 2), 'timeout': True}


CASES = []
for d in (164, 256, 512):
    CASES.append(('nest_paren_%d' % d, lambda d=d: gen_nested_paren(d), '嵌套括号 %d 层' % d))
for d in (164, 256):
    CASES.append(('nest_call_%d' % d, lambda d=d: gen_nested_call(d), '嵌套调用 %d 层' % d))
for d in (164, 256):
    CASES.append(('nest_sub_%d' % d, lambda d=d: gen_nested_subscript(d), '下标链 %d 层' % d))
for d in (90, 120):
    CASES.append(('nest_if_%d' % d, lambda d=d: gen_nested_if(d), 'if 缩进嵌套 %d 层' % d))
for d in (10, 30, 60, 90):
    CASES.append(('nest_if_var_%d' % d, lambda d=d: gen_nested_if_var(d),
                  'if 单子链嵌套 %d 层（仅叶子带副作用）' % d))
for n in (520, 1000, 2000):
    CASES.append(('stmts_%d' % n, lambda n=n: gen_stmts(n), '函数 %d 条语句' % n))
for n in (3000, 4000):
    CASES.append(('stmts_%d' % n, lambda n=n: gen_stmts(n), '函数 %d 条语句' % n))
for n in (5000, 20000):
    CASES.append(('giant_add_%d' % n, lambda n=n: gen_giant_add(n), '巨型加法链 %d 项' % n))
CASES.append(('giant_bool_5000', lambda: gen_giant_bool(5000), '巨型布尔链 5000 项'))
CASES.append(('giant_str_5000', lambda: gen_giant_str(5000), '巨型字符串拼接 5000 项'))
for n in (5000, 20000):
    CASES.append(('giant_list_%d' % n, lambda n=n: gen_giant_list(n), '巨型列表字面量 %d 项' % n))


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*', default=None)
    ap.add_argument('--out', default=os.path.join(LOGS, 'l4_boundary.json'))
    args = ap.parse_args()
    os.makedirs(BOUND, exist_ok=True)
    rows = []
    for name, gen, desc in CASES:
        if args.only and not any(name.startswith(p) for p in args.only):
            continue
        py = os.path.join(BOUND, name + '.py')
        pyc = os.path.join(BOUND, name + '.pyc')
        prod = os.path.join(BOUND, name + 'OK.py')
        src_text = gen()
        with open(py, 'w', encoding='utf-8', newline='\n') as f:
            f.write(src_text)
        rec = {'name': name, 'desc': desc, 'file': py,
               'src_lines': len(src_text.splitlines()), 'src_bytes': len(src_text)}
        # 1) 源码能否编译（CPython 自身的边界先于 pycdc）
        try:
            py_compile.compile(py, cfile=pyc, doraise=True)
            rec['src_compile'] = 'ok'
        except Exception as exc:
            rec['src_compile'] = '%s: %s' % (type(exc).__name__, str(exc)[:160])
        if rec['src_compile'] != 'ok':
            rec['pycdc'] = {'skipped': '源码不可编译'}
            rec['verdict'] = 'SOURCE_LIMIT'
            rows.append(rec)
            print('[bnd] %-18s 源码编译失败: %s' % (name, rec['src_compile'][:90]))
            continue
        # 2) pycdc
        if os.path.exists(prod):
            os.remove(prod)
        d = run([sys.executable, '-X', 'utf8', 'pycdc.py', pyc, '-o', prod], timeout=150)
        rec['pycdc'] = {'rc': d['rc'], 'elapsed': d['elapsed'], 'timeout': d['timeout'],
                        'stderr_tail': d['stderr'][-300:],
                        'product_bytes': os.path.getsize(prod) if os.path.exists(prod) else -1}
        if not os.path.exists(prod):
            rec['verdict'] = 'NO_PRODUCT'
            rows.append(rec)
            print('[bnd] %-18s pycdc 未产出 (rc=%s, %ss)' % (name, d['rc'], d['elapsed']))
            continue
        # 3) 产物可编译性 + 判据
        v = run([sys.executable, '-X', 'utf8', 'scripts/pyc_verify.py', 'single', pyc,
                 '--source', prod], timeout=150)
        status = None
        units = None
        for line in (v['stdout'] or '').splitlines():
            s = line.strip()
            if s.startswith('[single] status='):
                for part in s.split():
                    if part.startswith('status='):
                        status = part.split('=', 1)[1]
                    elif part.startswith('units='):
                        units = part.split('=', 1)[1]
        rec['verify'] = {'status': status, 'units': units, 'elapsed': v['elapsed']}
        # 4) AST 保真度
        try:
            st = ast.parse(src_text)
            pt = ast.parse(open(prod, encoding='utf-8', errors='replace').read())
            rec['fidelity'] = {'src_depth': ast_depth(st), 'prod_depth': ast_depth(pt),
                               'src_stmts': ast_stmts(st), 'prod_stmts': ast_stmts(pt)}
        except Exception as exc:
            rec['fidelity'] = {'error': '%s: %s' % (type(exc).__name__, exc)}
        # 5) 执行级比对
        s = run([sys.executable, '-X', 'utf8', '-c', RUNNER, py], timeout=60)
        o = run([sys.executable, '-X', 'utf8', '-c', RUNNER, prod], timeout=60)
        rec['exec'] = {'src_rc': s['rc'], 'prod_rc': o['rc'], 'src_out': s['stdout'][:200],
                       'prod_out': o['stdout'][:200], 'prod_err': o['stderr'][-200:],
                       'equal': s['stdout'] == o['stdout'] and s['rc'] == o['rc']}
        rec['verdict'] = 'OK' if rec['exec']['equal'] and status == 'success' else 'DEGRADED'
        rows.append(rec)
        print('[bnd] %-18s pycdc(rc=%s,%ss) verify=%-12s depth %s->%s stmts %s->%s exec_equal=%s' % (
            name, d['rc'], d['elapsed'], status,
            rec.get('fidelity', {}).get('src_depth'), rec.get('fidelity', {}).get('prod_depth'),
            rec.get('fidelity', {}).get('src_stmts'), rec.get('fidelity', {}).get('prod_stmts'),
            rec['exec']['equal']))
    with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'rows': rows}, f, ensure_ascii=False, indent=1)
    print('-> %d cases' % len(rows))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
