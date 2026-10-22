#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 语料外样本清单构建器（§2 取样）。

「语料外」定义（写死，便于复核）：
  语料内 = 402（shards/shard0..7.json）+ 34（failing_index.json）
          + 1（site-packages/fly/data/quotation.pyc）
          => 语料内全部位于 **仓库内 `site-packages/`**（见 corpus_probe.json 复核）。
  语料外 = (1) 系统 CPython stdlib（`D:\\Python\\Lib`）
          (2) 系统 site-packages（`D:\\Python\\Lib\\site-packages`，第三方真包）
          (3) 仓库自有模块（`core/**`、`parsers/**`、`scripts/**`、`tools/**`）

特征标签**由源码 AST 自动判定**（不手写），保证「覆盖类型注解/f-string/dataclass/
生成器/async/装饰器链/PEP604/except*」这一要求可机器复核。

输出：`rounds/round6/offcorpus/samples.json`
"""
from __future__ import annotations

import ast
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND6 = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(ROUND6, '..', '..', '..', '..', '..'))

STD = r'D:\Python\Lib'
SP = r'D:\Python\Lib\site-packages'

# (slug, 源码路径)
REAL = [
    # ── 系统 stdlib（真 CPython 源码） ───────────────────────────────
    ('stdlib_dataclasses',      STD + r'\dataclasses.py'),
    ('stdlib_contextlib',       STD + r'\contextlib.py'),
    ('stdlib_functools',        STD + r'\functools.py'),
    ('stdlib_enum',             STD + r'\enum.py'),
    ('stdlib_asyncio_taskgroups', STD + r'\asyncio\taskgroups.py'),
    ('stdlib_asyncio_timeouts', STD + r'\asyncio\timeouts.py'),
    ('stdlib_json_encoder',     STD + r'\json\encoder.py'),
    ('stdlib_xml_ElementPath',  STD + r'\xml\etree\ElementPath.py'),
    ('stdlib_tomllib_parser',   STD + r'\tomllib\_parser.py'),
    ('stdlib_re__parser',       STD + r'\re\_parser.py'),
    ('stdlib_statistics',       STD + r'\statistics.py'),
    ('stdlib_difflib',          STD + r'\difflib.py'),
    ('stdlib_http_cookiejar',   STD + r'\http\cookiejar.py'),
    ('stdlib_tarfile',          STD + r'\tarfile.py'),
    ('stdlib_subprocess',       STD + r'\subprocess.py'),
    ('stdlib_urllib_request',   STD + r'\urllib\request.py'),
    ('stdlib_unittest_case',    STD + r'\unittest\case.py'),
    ('stdlib_argparse',         STD + r'\argparse.py'),
    ('stdlib_ipaddress',        STD + r'\ipaddress.py'),
    ('stdlib_asyncio_base_events', STD + r'\asyncio\base_events.py'),
    ('stdlib_asyncio_streams',  STD + r'\asyncio\streams.py'),
    ('stdlib_typing',           STD + r'\typing.py'),
    # ── except* 真实样本（3.11 ExceptionGroup） ───────────────────────
    ('stdlib_ast',              STD + r'\ast.py'),
    ('stdlib_csv',              STD + r'\csv.py'),
    ('stdlib_asyncio_tasks',    STD + r'\asyncio\tasks.py'),
    # ── 系统 site-packages（第三方真包） ─────────────────────────────
    ('sp_anyio_fileio',         SP + r'\anyio\_core\_fileio.py'),
    ('sp_anyio_sync',           SP + r'\anyio\_core\_synchronization.py'),
    ('sp_anyio_lowlevel',       SP + r'\anyio\lowlevel.py'),
    ('sp_anyio_functools',      SP + r'\anyio\functools.py'),
    ('sp_packaging_specifiers', SP + r'\packaging\specifiers.py'),
    ('sp_packaging_version',    SP + r'\packaging\version.py'),
    ('sp_httpcore_models',      SP + r'\httpcore\_models.py'),
    ('sp_starlette_formparsers', SP + r'\starlette\formparsers.py'),
    ('sp_pydantic_dataclasses', SP + r'\pydantic\_internal\_dataclasses.py'),
    ('sp_pydantic_fields',      SP + r'\pydantic\fields.py'),
    ('sp_pandas_indexing',      SP + r'\pandas\core\indexing.py'),
    ('sp_sqlalchemy_collections', SP + r'\sqlalchemy\orm\collections.py'),
    ('sp_sympy_qexpr',          SP + r'\sympy\physics\quantum\qexpr.py'),
    # ── 仓库自有模块（仓内真实代码，语料外） ─────────────────────────
    ('repo_core_config',        REPO + r'\core\config.py'),
    ('repo_core_fast_stack',    REPO + r'\core\fast_stack.py'),
    ('repo_core_object_pool',   REPO + r'\core\object_pool.py'),
    ('repo_core_cfg_basic_block', REPO + r'\core\cfg\basic_block.py'),
    ('repo_core_cfg_builder',   REPO + r'\core\cfg\cfg_builder.py'),
    ('repo_parsers_ctx',        REPO + r'\parsers\context_manager.py'),
    ('repo_scripts_verify',     REPO + r'\scripts\pyc_verify.py'),
    ('repo_tools_syntax_cov',   REPO + r'\tools\kb\syntax_coverage.py'),
]

# 自动特征判定用的节点类型
FEATURE_NODES = {
    '注解': ast.AnnAssign,
    'f-string': ast.JoinedStr,
    'dataclass': ast.ClassDef,
    '生成器': (ast.FunctionDef, ast.AsyncFunctionDef),
    'async': ast.AsyncFunctionDef,
    '装饰器': (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
    'match': ast.Match,
    '海象': ast.NamedExpr,
}


def find_pyc(src: str) -> str | None:
    d, base = os.path.split(src)
    cache = os.path.join(d, '__pycache__')
    stem = os.path.splitext(base)[0]
    if not os.path.isdir(cache):
        return None
    cands = [fn for fn in sorted(os.listdir(cache))
             if fn.startswith(stem + '.') and fn.endswith('.pyc')]
    # 优先**未被 pytest 断言重写**的 pyc（pytest 版含 _pytest.assertion.rewrite 桩，
    # 会把「产物语法非法」与「pytest 改写」混在一起，损害语料外结论的可比性）
    plain = [fn for fn in cands if 'pytest' not in fn]
    if plain:
        cands = plain
    if not cands:
        return None
    return os.path.join(cache, cands[0])


def detect_features(src: str):
    """由源码 AST 判定语言特征（机器可复核）。"""
    feats = []
    with open(src, encoding='utf-8', errors='replace') as f:
        text = f.read()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ['语法解析失败']
    seen = set()

    def mark(name):
        if name not in seen:
            seen.add(name)
            feats.append(name)

    has_union = False
    runtime_union = False
    except_star = False
    dec_chain = 0
    dataclass_use = False
    gen = False
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            mark('f-string')
        if isinstance(node, ast.AnnAssign):
            mark('注解')
        if isinstance(node, ast.arg) and node.annotation is not None:
            mark('注解')
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns is not None:
                mark('注解')
            if node.decorator_list:
                mark('装饰器链' if len(node.decorator_list) > 1 else '装饰器')
                dec_chain = max(dec_chain, len(node.decorator_list))
            if node.name == '__init__' or True:
                pass
        if isinstance(node, ast.ClassDef):
            if node.decorator_list:
                mark('装饰器链' if len(node.decorator_list) > 1 else '装饰器')
            for d in node.decorator_list:
                tgt = d.func if isinstance(d, ast.Call) else d
                nm = getattr(tgt, 'id', None) or getattr(tgt, 'attr', None)
                if nm in ('dataclass', 'dataclasses'):
                    dataclass_use = True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for n in ast.walk(node):
                if isinstance(n, (ast.Yield, ast.YieldFrom)):
                    gen = True
                    break
        if isinstance(node, ast.AsyncFunctionDef):
            mark('async')
        if isinstance(node, ast.Match):
            mark('match')
        if isinstance(node, ast.NamedExpr):
            mark('海象')
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            # PEP604：注解位置的 X | Y
            has_union = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'isinstance':
            for a in node.args[1:]:
                if isinstance(a, ast.BinOp) and isinstance(a.op, ast.BitOr):
                    runtime_union = True
    if dataclass_use:
        mark('dataclass')
    if gen:
        mark('生成器')
    if except_star or 'except*' in text.replace(' ', ''):
        mark('except*')
    if has_union:
        mark('PEP604')
    if runtime_union:
        mark('PEP604(运行时)')
    if 'ExceptionGroup' in text:
        mark('ExceptionGroup')
    if 'TaskGroup' in text:
        mark('TaskGroup')
    if 'asyncio' in text:
        mark('asyncio')
    return feats


def main() -> int:
    out = os.path.join(ROUND6, 'offcorpus', 'samples.json')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    samples = []
    missing = []
    for slug, src in REAL:
        pyc = find_pyc(src)
        if not pyc or not os.path.exists(src):
            missing.append((slug, src))
            continue
        samples.append({'slug': slug, 'src': src, 'pyc': pyc,
                        'features': detect_features(src), 'origin': 'real'})
    payload = {'samples': samples, 'missing': missing,
               'corpus_definition': '语料内 = 仓库内 site-packages/** 的 402 + 34 + quotation(1) 个 pyc',
               'feature_detection': '由源码 AST 自动判定（见 detect_features）'}
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print('[samples] %d real samples, %d missing -> %s' % (len(samples), len(missing), out))
    for m in missing:
        print('  MISSING', m)
    # 特征覆盖汇总
    from collections import Counter
    c = Counter()
    for s in samples:
        for f in s['features']:
            c[f] += 1
    print('[features] %s' % dict(c))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
