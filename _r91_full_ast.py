#!/usr/bin/env python3
"""R91 full AST check - find the spurious return None"""
import sys, marshal, types, json
sys.path.insert(0, '.')
from core.cfg.region_ast_generator import generate_ast_from_regions
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

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

func_code = find_function(orig_code, 'get_price_common')
builder = CFGBuilder()
cfg = builder.build(func_code)
ast = generate_ast_from_regions(cfg)

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

func_ast = find_func_ast(ast, 'get_price_common')
if func_ast:
    body = func_ast.get('body', [])
    print(f"Function body: {len(body)} top-level statements")
    for i, stmt in enumerate(body):
        print(f"  [{i}] type={stmt.get('type')}")
        if stmt.get('type') == 'If':
            _check_if = stmt
            while _check_if:
                test = _check_if.get('test', {})
                print(f"      test: type={test.get('type')}", end="")
                if test.get('type') == 'Compare':
                    print(f" op={test.get('ops')}")
                elif test.get('type') == 'BoolOp':
                    print(f" op={test.get('op')}")
                else:
                    print()
                
                _body = _check_if.get('body', [])
                _orelse = _check_if.get('orelse', [])
                print(f"      body: {len(_body)} stmts -> {[s.get('type') for s in _body]}")
                
                if _orelse and len(_orelse) == 1 and _orelse[0].get('type') == 'If':
                    _check_if = _orelse[0]
                    print(f"      elif chain continues...")
                elif _orelse:
                    print(f"      orelse: {len(_orelse)} stmts -> {[s.get('type') for s in _orelse]}")
                    # Check if orelse has a return None
                    for s in _orelse:
                        if s.get('type') == 'Return':
                            val = s.get('value', {})
                            print(f"        RETURN value type={val.get('type') if val else None}")
                    _check_if = None
                else:
                    _check_if = None
