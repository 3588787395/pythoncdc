#!/usr/bin/env python3
"""R91 detailed AST dump to find spurious return None"""
import sys, marshal, types, json
sys.path.insert(0, '.')
from core.cfg.region_ast_generator import generate_ast_from_regions
from core.cfg.cfg_builder import CFGBuilder

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

def dump_ast(node, indent=0):
    if not isinstance(node, dict):
        return
    t = node.get('type', '?')
    prefix = '  ' * indent
    if t == 'If':
        test = node.get('test', {})
        print(f"{prefix}If (test={test.get('type')}):")
        for s in node.get('body', []):
            dump_ast(s, indent+1)
        orelse = node.get('orelse', [])
        if orelse:
            print(f"{prefix}else:")
            for s in orelse:
                dump_ast(s, indent+1)
    elif t == 'Return':
        val = node.get('value')
        val_type = val.get('type') if isinstance(val, dict) else None
        val_val = val.get('value') if isinstance(val, dict) else None
        print(f"{prefix}Return (value={val_type}, val={val_val})")
    elif t == 'Assign':
        targets = node.get('targets', [])
        tgt_names = []
        for tgt in targets:
            if tgt.get('type') == 'Name':
                tgt_names.append(tgt.get('id'))
            elif tgt.get('type') == 'Tuple':
                tgt_names.append('(' + ','.join(e.get('id','?') for e in tgt.get('elts',[])) + ')')
        val = node.get('value', {})
        print(f"{prefix}Assign targets={tgt_names} value={val.get('type')}")
    elif t == 'Expr':
        val = node.get('value', {})
        print(f"{prefix}Expr value={val.get('type')}")
    elif t == 'Global':
        print(f"{prefix}Global {node.get('names')}")
    else:
        print(f"{prefix}{t}")

func_ast = find_func_ast(ast, 'get_price_common')
if func_ast:
    for s in func_ast.get('body', []):
        dump_ast(s)
