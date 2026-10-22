#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 执行级差分的 probe 规格（§3）。

每个样例给出「同一输入序列」下的探针：表达式（返回值 + 类型）或代码块（副作用序）。
探针只调用**纯函数 / 只读 API**，不触网、不写文件、不起子进程（除 stdlib 自身惰性）。

输出：`rounds/round6/exec_probes.json`
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND6 = os.path.dirname(HERE)
OFF = os.path.join(ROUND6, 'offcorpus')

P = {}


def add(slug, dotted, probes):
    P[slug] = {'slug': slug, 'dotted': dotted, 'probes': probes}


add('stdlib_difflib', 'difflib', [
    {'label': 'SequenceMatcher.ratio', 'expr': "SequenceMatcher(None, 'abcd', 'bcde').ratio()"},
    {'label': 'SequenceMatcher.get_matching_blocks',
     'expr': "SequenceMatcher(None, 'abcd', 'abed').get_matching_blocks()"},
    {'label': 'SequenceMatcher.get_opcodes', 'expr': "SequenceMatcher(None, 'abcd', 'abed').get_opcodes()"},
    {'label': 'get_close_matches', 'expr': "get_close_matches('appel', 'ape')"},
    {'label': 'unified_diff', 'expr': "unified_diff(['a\\n', 'b\\n'], ['a\\n', 'c\\n'])"},
    {'label': 'ndiff', 'expr': "ndiff(['a', 'b'], ['a', 'c'])"},
    {'label': 'set_seq2 后 ratio', 'code':
     "m = SequenceMatcher(None, 'abc', 'bcd')\n"
     "m.set_seq2('xyz')\n"
     "print(m.ratio())\n"},
])

add('stdlib_dataclasses', 'dataclasses', [
    {'label': 'dataclass(order=True,eq=False) 冲突检查', 'code':
     "from dataclasses import dataclass\n"
     "try:\n"
     "    @dataclass(order=True, eq=False)\n"
     "    class C:\n"
     "        a: int\n"
     "    print('NO-ERROR')\n"
     "except ValueError as e:\n"
     "    print('ValueError:', e)\n"},
    {'label': 'asdict', 'code':
     "from dataclasses import dataclass, asdict\n"
     "@dataclass\n"
     "class D:\n"
     "    a: int = 1\n"
     "    b: str = 'x'\n"
     "print(asdict(D(2)))\n"},
    {'label': 'fields 元数据', 'code':
     "from dataclasses import dataclass, fields\n"
     "@dataclass\n"
     "class E:\n"
     "    a: int = 1\n"
     "print([(f.name, f.type, f.default) for f in fields(E)])\n"
     "print(E.__dataclass_fields__['a'].type)\n"},
    {'label': 'slots=True', 'code':
     "from dataclasses import dataclass\n"
     "@dataclass(slots=True)\n"
     "class F:\n"
     "    a: int = 1\n"
     "print(F.__slots__)\n"
     "print(F(3).a)\n"},
    {'label': 'eq/repr', 'code':
     "from dataclasses import dataclass\n"
     "@dataclass\n"
     "class G:\n"
     "    a: int = 1\n"
     "print(G(1) == G(1), repr(G(1)))\n"},
])

add('stdlib_contextlib', 'contextlib', [
    {'label': 'contextmanager 副作用序', 'code':
     "from contextlib import contextmanager\n"
     "@contextmanager\n"
     "def cm():\n"
     "    print('enter')\n"
     "    yield 1\n"
     "    print('exit')\n"
     "with cm() as v:\n"
     "    print('body', v)\n"},
    {'label': 'suppress', 'code':
     "from contextlib import suppress\n"
     "with suppress(ValueError):\n"
     "    raise ValueError('x')\n"
     "print('suppressed')\n"},
    {'label': 'ExitStack 逆序退出', 'code':
     "from contextlib import ExitStack\n"
     "class CM:\n"
     "    def __init__(self, n): self.n = n\n"
     "    def __enter__(self): print('enter', self.n); return self\n"
     "    def __exit__(self, *a): print('exit', self.n); return False\n"
     "with ExitStack() as st:\n"
     "    st.enter_context(CM(1))\n"
     "    st.enter_context(CM(2))\n"
     "print('done')\n"},
])

add('stdlib_functools', 'functools', [
    {'label': 'reduce', 'expr': "reduce(lambda a, b: a + b, [1, 2, 3])"},
    {'label': 'partial', 'expr': "partial(lambda a, b: a + b, 1)(2)"},
    {'label': 'lru_cache', 'expr': "lru_cache(maxsize=None)(lambda x: x * 2)(3)"},
    {'label': 'wraps 元数据', 'code':
     "from functools import wraps\n"
     "def deco(f):\n"
     "    @wraps(f)\n"
     "    def inner(*a, **k):\n"
     "        return f(*a, **k) * 2\n"
     "    return inner\n"
     "@deco\n"
     "def f(x):\n"
     "    'doc'\n"
     "    return x + 1\n"
     "print(f(3), f.__name__, f.__doc__)\n"},
])

add('stdlib_json_encoder', 'json.encoder', [
    {'label': 'JSONEncoder().encode', 'expr': "JSONEncoder().encode({'a': [1, 2], 'b': None, 'c': True})"},
    {'label': 'sort_keys+indent', 'expr': "JSONEncoder(sort_keys=True, indent=2).encode({'b': 1, 'a': 2})"},
    {'label': 'default=str', 'expr': "JSONEncoder(default=str).encode({1: 2})"},
])

add('stdlib_ipaddress', 'ipaddress', [
    {'label': 'ip_address', 'expr': "ip_address('192.168.0.1')"},
    {'label': 'ip_network', 'expr': "ip_network('10.0.0.0/8')"},
    {'label': 'is_private', 'expr': "ip_address('192.168.0.1').is_private"},
    {'label': 'address_exclude 版本冲突异常', 'code':
     "from ipaddress import ip_network\n"
     "try:\n"
     "    ip_network('10.0.0.0/8').address_exclude(ip_network('192.168.0.0/24'))\n"
     "except TypeError as e:\n"
     "    print('TypeError:', e)\n"},
])

add('stdlib_argparse', 'argparse', [
    {'label': 'parse_args 正常路径', 'code':
     "from argparse import ArgumentParser\n"
     "p = ArgumentParser(prog='t')\n"
     "p.add_argument('--x', type=int)\n"
     "p.add_argument('--y', default='d')\n"
     "a = p.parse_args(['--x', '3'])\n"
     "print(a.x, a.y)\n"},
    {'label': '未知参数异常', 'code':
     "from argparse import ArgumentParser\n"
     "p = ArgumentParser(prog='t')\n"
     "p.add_argument('--x', type=int)\n"
     "try:\n"
     "    p.parse_args(['--zz'])\n"
     "except SystemExit as e:\n"
     "    print('SystemExit', e.code)\n"},
])

add('stdlib_subprocess', 'subprocess', [
    {'label': 'list2cmdline', 'expr': "list2cmdline(['a b', 'c'])"},
    {'label': 'TimeoutExpired 类型', 'expr': "TimeoutExpired.__name__"},
])

add('stdlib_tarfile', 'tarfile', [
    {'label': 'TarInfo.tobuf', 'code':
     "from tarfile import TarInfo\n"
     "t = TarInfo('x.txt')\n"
     "t.size = 3\n"
     "print(t.tobuf())\n"
     "print(t.name, t.type, t.size)\n"},
    {'label': 'TarInfo 默认 type', 'expr': "TarInfo('n').type"},
])

add('stdlib_typing', 'typing', [
    {'label': 'get_args(Union)', 'expr': "get_args(Union[int, str])"},
    {'label': 'Optional[int]', 'expr': "Optional[int]"},
    {'label': 'get_type_hints', 'code':
     "def f(x: int) -> str:\n"
     "    return str(x)\n"
     "print(get_type_hints(f))\n"},
])

add('stdlib_statistics', 'statistics', [
    {'label': 'mean', 'expr': "mean([1, 2, 3])"},
    {'label': 'median', 'expr': "median([1, 3, 2])"},
    {'label': 'NormalDist.zscore', 'expr': "NormalDist(1, 2).zscore(3)"},
    {'label': 'variance', 'expr': "variance([1, 2, 3, 4])"},
])

add('stdlib_csv', 'csv', [
    {'label': 'Sniffer.has_header', 'code':
     "import csv\n"
     "s = 'a,b\\n1,2\\n3,4\\n'\n"
     "sn = csv.Sniffer()\n"
     "print(sn.has_header(s))\n"
     "print(sn.sniff(s).delimiter)\n"},
])

add('stdlib_xml_ElementPath', 'xml.etree.ElementPath', [
    {'label': 'findall', 'code':
     "import xml.etree.ElementTree as ET\n"
     "el = ET.fromstring('<root><b id=\"1\">x</b><b id=\"2\">y</b></root>')\n"
     "print(findall(el, './/b'))\n"},
])

add('stdlib_tomllib_parser', 'tomllib._parser', [
    {'label': 'loads', 'expr': "loads('a = 1\\nb = \"x\"')"},
])

add('stdlib_re__parser', 're._parser', [
    {'label': 'parse groupindex', 'expr': "parse('(?P<x>a)|b', 0).groupindex"},
])

add('stdlib_http_cookiejar', 'http.cookiejar', [
    {'label': 'user_domain_match', 'expr': "user_domain_match('www.example.com', '.example.com')"},
    {'label': 'CookieJar/Policy 构造', 'code':
     "from http.cookiejar import CookieJar, DefaultCookiePolicy\n"
     "j = CookieJar()\n"
     "p = DefaultCookiePolicy()\n"
     "print(type(j).__name__, p.set_ok_verifiability)\n"},
])

add('stdlib_unittest_case', 'unittest.case', [
    {'label': 'assertEqual 失败信息', 'code':
     "import unittest\n"
     "class T(unittest.TestCase):\n"
     "    def runTest(self):\n"
     "        pass\n"
     "t = T()\n"
     "try:\n"
     "    t.assertEqual(1, 2)\n"
     "except AssertionError as e:\n"
     "    print('AssertionError:', e)\n"},
])

add('stdlib_asyncio_timeouts', 'asyncio.timeouts', [
    {'label': 'asyncio.timeout 超时', 'code':
     "import asyncio\n"
     "async def main():\n"
     "    try:\n"
     "        async with asyncio.timeout(0.01):\n"
     "            await asyncio.sleep(1)\n"
     "    except TimeoutError:\n"
     "        print('TimeoutError raised')\n"
     "    print('after')\n"
     "asyncio.run(main())\n"},
])

add('stdlib_asyncio_taskgroups', 'asyncio.taskgroups', [
    {'label': 'TaskGroup 正常', 'code':
     "import asyncio\n"
     "async def main():\n"
     "    async with asyncio.TaskGroup() as tg:\n"
     "        tg.create_task(asyncio.sleep(0.01))\n"
     "    print('tg done')\n"
     "asyncio.run(main())\n"},
])

add('stdlib_asyncio_streams', 'asyncio.streams', [
    {'label': 'StreamReader.read', 'code':
     "import asyncio\n"
     "async def main():\n"
     "    r = asyncio.StreamReader()\n"
     "    r.feed_data(b'hello')\n"
     "    r.feed_eof()\n"
     "    print(await r.read())\n"
     "    print(await r.readline())\n"
     "asyncio.run(main())\n"},
])

add('sp_httpcore_models', 'httpcore._models', [
    {'label': 'URL 构造', 'expr': "URL('http://example.com/x')"},
    {'label': 'Request 构造', 'expr': "Request('GET', 'http://example.com').method"},
])

add('repo_core_config', 'core_config', [
    {'label': 'Config 状态', 'expr': "(Config.is_cfg_enabled(), Config.is_hybrid_mode())"},
    {'label': 'enable/disable 往返', 'code':
     "print(enable_cfg(verbose=False))\n"
     "print(Config.is_cfg_enabled(), Config.is_hybrid_mode())\n"
     "print(disable_cfg())\n"
     "print(Config.is_cfg_enabled())\n"},
])

add('repo_core_object_pool', 'core_object_pool', [
    {'label': 'ObjectPool acquire/stats', 'code':
     "from collections import deque\n"
     "p = ObjectPool(lambda: deque(), max_size=2)\n"
     "a = p.acquire()\n"
     "print(type(a).__name__, sorted(p.get_stats().keys()))\n"},
    {'label': 'NodeOperationContext', 'code':
     "with NodeOperationContext() as c:\n"
     "    print(type(c).__name__)\n"
     "print('ctx-ok')\n"},
])

add('repo_parsers_ctx', 'parsers_context_manager', [
    {'label': 'push/pop context', 'code':
     "cm = ContextManager()\n"
     "info = cm.push_context(ContextType.FUNCTION, 'f1')\n"
     "print(info.name, cm.current_context_type())\n"
     "print(cm.get_context_path())\n"
     "print(cm.is_in_context(ContextType.FUNCTION))\n"},
])


def main() -> int:
    samples = json.load(open(os.path.join(OFF, 'samples.json'), encoding='utf-8'))['samples']
    byslug = {s['slug']: s for s in samples}
    out = []
    for slug, spec in P.items():
        if slug not in byslug:
            print('SKIP (不在样本清单): %s' % slug)
            continue
        s = byslug[slug]
        out.append({'slug': slug, 'dotted': spec['dotted'], 'pyc': s['pyc'],
                    'src': s['src'], 'probes': spec['probes']})
    path = os.path.join(ROUND6, 'exec_probes.json')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'samples': out}, f, ensure_ascii=False, indent=1)
    print('-> %s (%d samples, %d probes)' % (path, len(out), sum(len(x['probes']) for x in out)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
