#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 语料外失败样本的**最小复现**（§2 要求：逐个失败给出最小复现）。

做法：把每个失败样本归到一个**根因类**，为每个类写一个**自包含最小样例**，
再用同一套命令跑（pycdc → pyc_verify → 执行级比对）：
    python -X utf8 pycdc.py <pyc> -o <base>OK.py
    python -X utf8 scripts/pyc_verify.py single <pyc> --source <产物>
    执行：分别 import 原模块 / 产物，调用 main()，比对 stdout。

每个最小样例都必须定义 main()（打印可观测结果），便于自动比对。

输出：logs/l4_repro.json + repro/*OK.py
"""
from __future__ import annotations

import argparse
import json
import os
import py_compile
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND6 = os.path.dirname(HERE)
LOGS = os.path.join(ROUND6, 'logs')
REPRO = os.path.join(ROUND6, 'repro')
REPO = os.path.abspath(os.path.join(ROUND6, '..', '..', '..', '..', '..'))

REPROS = {
    # C1 元组解包赋值丢失 → 后续读局部名变全局查找（difflib b2j/besti/bestj/la/answer）
    'c1_tuple_unpack': '''\
def f(a, b):
    x, y, z = a, b, 0
    return (x, y, z)


def main():
    try:
        print(f(1, 2))
    except BaseException as e:
        print('EXC', type(e).__name__, e)
''',
    # C2 前置校验（raise）被删除 → 错误输入被静默接受（dataclasses eq/order 冲突）
    'c2_check_dropped': '''\
def f(order, eq):
    if order and not eq:
        raise ValueError('eq must be true if order is true')
    return 'accepted'


def main():
    try:
        print(f(True, False))
    except BaseException as e:
        print('EXC', type(e).__name__, e)
''',
    # C3 return 语句丢失 → 恒返回 None（core/cfg/cfg_builder.py ControlFlowGraph.to_dict）
    'c3_return_dropped': '''\
def to_dict(self):
    data = {'name': 'x', 'size': 1}
    return data


def main():
    print(to_dict(object()))
''',
    # C4 分支极性反转（JUMP_IF_TRUE_OR_POP → JUMP_IF_FALSE_OR_POP）
    'c4_polarity_flip': '''\
def f(a, b):
    if a and b:
        return 'both'
    return 'not-both'


def main():
    print(f(True, True))
    print(f(True, False))
''',
    # C5 await 路径丢失（async）
    'c5_await_dropped': '''\
import asyncio


async def inner(x):
    await asyncio.sleep(0)
    return x * 2


async def outer(x):
    y = await inner(x)
    return y


def main():
    try:
        print(asyncio.run(outer(3)))
    except BaseException as e:
        print('EXC', type(e).__name__, e)
''',
    # C6 形参/返回注解丢失（__annotations__ 语义）
    'c6_annotation_dropped': '''\
def f(x: int, y: str = 'a') -> str:
    return str(x) + y


def main():
    print(f(1))
    print(f.__annotations__)
''',
    # C7 类属性/字段丢失（httpcore._models.URL.port）
    'c7_class_attr_lost': '''\
class URL:
    def __init__(self, url):
        self.scheme = 'http'
        self.port = None
        self.target = url


def main():
    u = URL('/x')
    print(u.scheme, u.port, u.target)
''',
    # C8 局部变量未绑定（UnboundLocalError：csv Sniffer.start / tomllib char）
    'c8_unbound_local': '''\
def f(cond):
    if cond:
        start = 0
    return start


def main():
    try:
        print(f(False))
    except BaseException as e:
        print('EXC', type(e).__name__, e)
''',
    # C9 下标/切片丢失
    'c9_slice_lost': '''\
def f(s):
    return s[1:3]


def main():
    try:
        print(f('abcd'))
    except BaseException as e:
        print('EXC', type(e).__name__, e)
''',
    # C10 装饰器链 / dataclass 装饰器应用次序
    'c10_decorator_chain': '''\
def deco_a(f):
    def inner(*a, **k):
        return ('a', f(*a, **k))
    return inner


def deco_b(f):
    def inner(*a, **k):
        return ('b', f(*a, **k))
    return inner


@deco_a
@deco_b
def g(x):
    return x


def main():
    print(g(1))
''',
}


def run(cmd, timeout=120, cwd=REPO):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                           errors='replace', timeout=timeout, cwd=cwd)
        return {'rc': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except subprocess.TimeoutExpired:
        return {'rc': None, 'stdout': '', 'stderr': 'TIMEOUT'}


def exec_main(path, timeout=30):
    """import 模块并调用 main()，捕获 stdout。"""
    code = (
        "import importlib.util, sys, io\n"
        "spec = importlib.util.spec_from_file_location('m', sys.argv[1])\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "sys.modules['m'] = m\n"
        "spec.loader.exec_module(m)\n"
        "m.main()\n"
    )
    p = subprocess.run([sys.executable, '-X', 'utf8', '-c', code, path],
                       capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=timeout, cwd=REPO)
    return {'rc': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*', default=None)
    args = ap.parse_args()
    os.makedirs(REPRO, exist_ok=True)
    rows = []
    for name, src in REPROS.items():
        if args.only and name not in args.only:
            continue
        py = os.path.join(REPRO, name + '.py')
        pyc = os.path.join(REPRO, name + '.pyc')
        prod = os.path.join(REPRO, name + 'OK.py')
        with open(py, 'w', encoding='utf-8', newline='\n') as f:
            f.write(src)
        if os.path.exists(prod):
            os.remove(prod)
        try:
            py_compile.compile(py, cfile=pyc, doraise=True)
        except Exception as exc:
            rows.append({'name': name, 'error': str(exc)})
            continue
        d = run([sys.executable, '-X', 'utf8', 'pycdc.py', pyc, '-o', prod])
        v = run([sys.executable, '-X', 'utf8', 'scripts/pyc_verify.py', 'single', pyc,
                 '--source', prod]) if os.path.exists(prod) else {'stdout': '', 'rc': None}
        status = None
        for line in (v['stdout'] or '').splitlines():
            if line.strip().startswith('[single] status='):
                for part in line.split():
                    if part.startswith('status='):
                        status = part.split('=', 1)[1]
        s = exec_main(py)
        o = exec_main(prod) if os.path.exists(prod) else {'rc': None, 'stdout': '', 'stderr': 'NO-PRODUCT'}
        same = (s['stdout'] == o['stdout']) and (s['rc'] == o['rc'])
        rows.append({'name': name, 'pyc': pyc, 'product': prod,
                     'pycdc_rc': d['rc'], 'verify_status': status,
                     'src_stdout': s['stdout'], 'prod_stdout': o['stdout'],
                     'src_rc': s['rc'], 'prod_rc': o['rc'],
                     'exec_equal': same,
                     'prod_stderr_tail': (o.get('stderr') or '')[-200:]})
        print('[repro] %-22s verify=%-13s exec_equal=%s' % (name, status, same))
        if not same:
            print('        src : %r' % s['stdout'][:120])
            print('        prod: %r  %s' % (o['stdout'][:120], (o.get('stderr') or '')[-120:]))
    with open(os.path.join(LOGS, 'l4_repro.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'rows': rows}, f, ensure_ascii=False, indent=1)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
