#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L3 执行级语义差分（迷你版；Task 9 `semantic_diff.py` 的前置原型）。

用途：`scripts/pyc_verify.py` 只比字节码/CFG，**从不执行**（baseline/judge_criteria.md
§3 B-01）。本脚本在**同一输入序列**下分别执行「探针源」与「pycdc 产物」，
比对返回值与可观测副作用（`with` 的 __enter__/__exit__ 次数、列表内容），
以判定「判定器判绿 ⇒ 语义等价」这条推断链是否成立。

实现要点（均为本轮踩坑后的修正）：
  - 每侧在**独立子进程**中执行（`--worker` 模式）：产物可能引入**死循环**
    （例：handler 内 continue 被丢弃 ⇒ while 宿主不前进），父进程用 timeout 兜底，
    记为 TIMEOUT（本身就是语义差的一种表现）。
  - 上下文管理器对象在**返回值**中必须归一化（否则两侧是不同实例 ⇒ 假阳性）。
  - 两侧各自**新建**上下文管理器 ⇒ 日志不串味。

用法：
    python -X utf8 l3_semdiff.py <probe_name> <func_name> [<func_name> ...]
    python -X utf8 l3_semdiff.py --worker <pyfile> <func> <case_json>
"""
import argparse
import asyncio
import importlib.util
import inspect
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
PROBES = os.path.abspath(os.path.join(HERE, '..', 'probes'))


class Ctx:
    """可观测的上下文管理器（记录 __enter__/__exit__ 配对）。"""

    def __init__(self, name='ctx'):
        self.name = name

    def __enter__(self):
        LOG.append(('enter', self.name))
        return self

    def __exit__(self, *exc):
        LOG.append(('exit', self.name))
        return False


class AsyncCtx(Ctx):
    async def __aenter__(self):
        LOG.append(('aenter', self.name))
        return self

    async def __aexit__(self, *exc):
        LOG.append(('aexit', self.name))
        return False


class Res:
    """async 资源桩：可作 async with 宿主，且提供 read/flush/get 协程。"""

    def __init__(self):
        self.name = 'res'

    async def __aenter__(self):
        LOG.append(('aenter', self.name))
        return self

    async def __aexit__(self, *exc):
        LOG.append(('aexit', self.name))
        return False

    async def read(self):
        LOG.append(('read', self.name))
        return 'R'

    async def flush(self):
        LOG.append(('flush', self.name))
        return 'F'

    async def get(self, x):
        LOG.append(('get', self.name))
        return 'G%s' % (x,)


LOG = []


def norm(v):
    """归一化：Ctx/AsyncCtx/Res 实例 → 名称；list/tuple/dict 递归。"""
    if isinstance(v, (Ctx, AsyncCtx, Res)):
        return '<%s:%s>' % (type(v).__name__, v.name)
    if isinstance(v, list):
        return [norm(x) for x in v]
    if isinstance(v, tuple):
        return tuple(norm(x) for x in v)
    if isinstance(v, dict):
        return {k: norm(x) for k, x in v.items()}
    return v


def build_args(spec):
    """按用例规格构造实参；ctx 规格形如 {'ctx': 1} 表示建 1 个上下文管理器。"""
    args = []
    for item in spec['args']:
        if isinstance(item, dict) and 'ctx' in item:
            args.append(AsyncCtx() if item.get('async') else Ctx())
        elif isinstance(item, dict) and 'res' in item:
            args.append(Res())
        else:
            args.append(item)
    return args


def worker(pyfile, func, spec):
    del LOG[:]
    mod = load(pyfile, 'w_' + os.path.basename(pyfile).replace('.', '_'))
    fn = getattr(mod, func, None)
    if fn is None:
        print(json.dumps({'error': 'missing_function'}))
        return 0
    args = build_args(spec)
    try:
        if inspect.iscoroutinefunction(fn):
            res = asyncio.run(fn(*args))
        else:
            res = fn(*args)
        out = {'kind': 'return', 'value': norm(res), 'log': list(LOG)}
    except Exception as exc:  # noqa: BLE001
        out = {'kind': 'raise', 'value': type(exc).__name__ + ': ' + str(exc), 'log': list(LOG)}
    print(json.dumps(out, ensure_ascii=False, default=str))
    return 0


def load(path, modname):
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


def run_side(pyfile, func, spec, timeout=20):
    cmd = [sys.executable, '-X', 'utf8', os.path.abspath(__file__),
           '--worker', pyfile, func, json.dumps(spec, ensure_ascii=False)]
    try:
        p = subprocess.run(cmd, capture_output=True, encoding='utf-8',
                           errors='replace', timeout=timeout)
    except subprocess.TimeoutExpired:
        return {'kind': 'TIMEOUT', 'value': None, 'log': []}
    out = (p.stdout or '').strip()
    if not out:
        return {'kind': 'ERROR', 'value': (p.stderr or '')[-300:], 'log': []}
    try:
        return json.loads(out.splitlines()[-1])
    except ValueError:
        return {'kind': 'ERROR', 'value': out[-300:], 'log': []}


def case_specs(probe, func):
    """按 (probe, func) 给出用例规格列表（多组输入以暴露被补偿掩盖的差异）。"""
    if probe.startswith('l3_o6'):
        return [{'args': [[3, -2, 5], {'ctx': 1}]}]
    if probe.startswith('l3_o4'):
        if func == 'o4':
            return [{'args': [[[1, 4], [7, 2]], {'ctx': 1}]}]
        return [{'args': [[3, -2], {'ctx': 1}]}, {'args': [[0, 4, 9], {'ctx': 1}]}]
    if probe.startswith('l3_o1'):
        if func == 'o1':
            return [{'args': [[3, -1], {'res': 1}, {'ctx': 1, 'async': True}]}]
        return [{'args': [[3, -1], {'res': 1}]}]
    if probe.startswith('l3_g1'):
        if func == 'r2_lt':
            return [{'args': [[5, -2, 7], True]}, {'args': [[5, -2, 7], False]}]
        # (a or b) and (c if a else (b or c))：a=False 时源与产物必然分叉
        return [{'args': [True, False, True]}, {'args': [False, True, True]},
                {'args': [False, False, True]}, {'args': [True, True, False]}]
    if probe.startswith('l3_g5c'):
        return [{'args': [[3, -1, 4]]}, {'args': [[3, -1, 4, 5, 6]]}]
    if probe.startswith('l3_g5b') or probe.startswith('l3_g5'):
        return [{'args': [[3, -1, 4]]}, {'args': [[3, -1, 4, 5]]}, {'args': [[-1, -2]]}]
    if probe.startswith('l3_g6'):
        if func == 'r7_del_ternary_slice':
            return [{'args': [[0, 1, 2, 3, 4], [0, 1]]}]
        return [{'args': [[0, 1, 2, 3, 4], [0, 1], 10]}]
    if probe.startswith('l3_g7d'):
        return [{'args': [[1]]}, {'args': [[1, 2, 3]]}, {'args': [[-1, 2]]}]
    if probe.startswith('l3_g7c') or probe.startswith('l3_g7'):
        return [{'args': [[1, 0, -1]]}]
    if probe.startswith('l3_b142'):
        return [{'args': [[0, 2, 5]]}, {'args': [[1, 0, 3]]}]
    if probe.startswith('l3_b143b') or probe.startswith('l3_b143'):
        return [{'args': [5]}, {'args': [2]}]
    if probe.startswith('l3_g3'):
        if func == 'r4_asyncwith':
            return [{'args': [{'res': 1}]}]
        return [{'args': [[3, -1], {'res': 1}]}]
    if probe.startswith('l3_g2'):
        return [{'args': [[3, -1]]}, {'args': [[1, 2, 3]]}]
    if probe.startswith('l3_g4'):
        return [{'args': [[1, 2, 3]]}, {'args': [{'k': 1, 'v': 2}]}]
    if probe.startswith('l3_o2'):
        return [{'args': [{'res': 1}, True, 3]}, {'args': [{'res': 1}, False, 3]}]
    if probe.startswith('l3_o3'):
        return [{'args': [[3, -1, 4]]}, {'args': [[]]}]
    if probe.startswith('l3_o5'):
        return [{'args': [[0, 1, 2, 3, 4], [0, 1], 10]}]
    return [{'args': [[1, 2, 3]]}]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--worker', nargs=3, metavar=('PYFILE', 'FUNC', 'CASEJSON'))
    ap.add_argument('probe', nargs='?')
    ap.add_argument('funcs', nargs='*')
    a = ap.parse_args()
    if a.worker:
        pyfile, func, casejson = a.worker
        return worker(pyfile, func, json.loads(casejson))
    src_path = os.path.join(PROBES, a.probe + '.py')
    ok_path = os.path.join(PROBES, a.probe + 'OK.py')
    rows = []
    for fn in a.funcs:
        for spec in case_specs(a.probe, fn):
            s = run_side(src_path, fn, spec)
            o = run_side(ok_path, fn, spec)
            same_val = s.get('value') == o.get('value') and s.get('kind') == o.get('kind')
            same_log = s.get('log') == o.get('log')
            verdict = 'EQUAL' if (same_val and same_log) else 'DIFFERENT'
            rows.append({'func': fn, 'source': s, 'product': o,
                         'value_equal': same_val, 'side_effect_equal': same_log,
                         'verdict': verdict})
    for r in rows:
        print(json.dumps(r, ensure_ascii=False, default=str))
    ndiff = sum(1 for r in rows if r['verdict'] == 'DIFFERENT')
    print('-> %s : %d/%d DIFF' % (a.probe, ndiff, len(rows)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
