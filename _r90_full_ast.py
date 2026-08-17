#!/usr/bin/env python3
"""R90 查看完整函数 AST"""
import sys, os, marshal, types, json
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator, generate_ast_from_regions

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

def find_function(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            inner = find_function(const, name)
            if inner:
                return inner
    return None

func_code = find_function(orig_code, 'get_kline_by_count_new')
if not func_code:
    print("Function not found!")
    sys.exit(1)

builder = CFGBuilder()
cfg = builder.build(func_code)

# Generate full function AST
ast = generate_ast_from_regions(cfg)

# Find the function def in the AST
def find_func_ast(node, name):
    if isinstance(node, dict):
        if node.get('type') == 'FunctionDef' and node.get('name') == name:
            return node
        for v in node.values():
            result = find_func_ast(v, name)
            if result:
                return result
    elif isinstance(node, list):
        for item in node:
            result = find_func_ast(item, name)
            if result:
                return result
    return None

func_ast = find_func_ast(ast, 'get_kline_by_count_new')
if func_ast:
    body = func_ast.get('body', [])
    print(f"Function body has {len(body)} top-level statements")
    for i, stmt in enumerate(body[:10]):
        print(f"\n[{i}] type={stmt.get('type')}")
        if stmt.get('type') == 'Assign':
            targets = stmt.get('targets', [])
            for j, t in enumerate(targets):
                print(f"  target[{j}]: type={t.get('type')}")
                if t.get('type') == 'Tuple':
                    for k, e in enumerate(t.get('elts', [])):
                        print(f"    elt[{k}]: type={e.get('type')}, id={e.get('id')}")
                elif t.get('type') == 'Name':
                    print(f"    id={t.get('id')}")
            value = stmt.get('value', {})
            print(f"  value: type={value.get('type')}")
            if value.get('type') == 'Call':
                func = value.get('func', {})
                print(f"  func: type={func.get('type')}, id={func.get('id')}")
        elif stmt.get('type') == 'If':
            test = stmt.get('test', {})
            print(f"  test: type={test.get('type')}")
            if test.get('type') == 'BoolOp':
                print(f"  op={test.get('op')}")
                for v in test.get('values', []):
                    print(f"    value: type={v.get('type')}")
            body_len = len(stmt.get('body', []))
            orelse_len = len(stmt.get('orelse', []))
            print(f"  body={body_len} stmts, orelse={orelse_len} stmts")
else:
    print("Function AST not found!")
    print(json.dumps(ast, default=str, indent=2)[:2000])
