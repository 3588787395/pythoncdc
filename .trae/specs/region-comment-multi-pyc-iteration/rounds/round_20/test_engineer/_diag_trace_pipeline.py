"""R20 diag: trace full pycdc pipeline for user_print signature."""
import sys
import types
import marshal
import json

sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

PYC = r'F:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/__init__.pyc'

with open(PYC, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg import build_cfg
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator

cfg_mod = build_cfg(code)
gen_mod = RegionASTGenerator(cfg_mod, top_level_code=code if code.co_name == '<module>' else None)
ast_dict = gen_mod.generate()

# Print user_print AST dict args
def find_node(node, name):
    if isinstance(node, dict):
        if node.get('type') == 'FunctionDef' and node.get('name') == name:
            return node
        for v in node.values():
            r = find_node(v, name)
            if r is not None:
                return r
    elif isinstance(node, list):
        for item in node:
            r = find_node(item, name)
            if r is not None:
                return r
    return None

up = find_node(ast_dict, 'user_print')
print('1. AST dict args:', json.dumps(up.get('args'), default=str))

# Convert to py_ast
converter = CFGASTConverter()

# Monkey-patch _convert_function_def to trace
orig_cfd = converter._convert_function_def
def traced_cfd(node_dict):
    if node_dict.get('name') == 'user_print':
        print('2. _convert_function_def input args:', json.dumps(node_dict.get('args'), default=str))
    result = orig_cfd(node_dict)
    if node_dict.get('name') == 'user_print':
        print('3. _convert_function_def output:')
        print('   type:', type(result).__name__)
        print('   _vararg:', getattr(result, '_vararg', 'MISSING'))
        print('   _kwarg:', getattr(result, '_kwarg', 'MISSING'))
        print('   _args:', getattr(result, '_args', 'MISSING'))
        print('   _kwonlyargs:', getattr(result, '_kwonlyargs', 'MISSING'))
        print('   _kw_defaults:', getattr(result, '_kw_defaults', 'MISSING'))
        print('   _defaults:', getattr(result, '_defaults', 'MISSING'))
    return result
converter._convert_function_def = traced_cfd

py_ast = converter.convert(ast_dict)

# Find user_print in py_ast by walking the body (avoid ASTBlock issues)
import ast as pyast
def find_funcdef(node, name):
    if isinstance(node, pyast.AST):
        if isinstance(node, pyast.FunctionDef) and node.name == name:
            return node
        for fname, fval in pyast.iter_fields(node):
            r = find_funcdef(fval, name)
            if r is not None:
                return r
    elif isinstance(node, list):
        for item in node:
            r = find_funcdef(item, name)
            if r is not None:
                return r
    return None

# py_ast might not be a standard ast.Module — check
print('\n4. py_ast type:', type(py_ast).__name__)
print('   py_ast attrs:', [a for a in dir(py_ast) if not a.startswith('__')][:20])

# Generate source
code_gen = CFGCodeGenerator()

# Monkey-patch _generate_function_def to trace
orig_gfd = CFGCodeGenerator._generate_function_def
def traced_gfd(self, node):
    if getattr(node, '_name', None) == 'user_print' or (hasattr(node, 'name') and node.name == 'user_print'):
        print('\n5. _generate_function_def input:')
        print('   _vararg:', getattr(node, '_vararg', 'MISSING'))
        print('   _kwarg:', getattr(node, '_kwarg', 'MISSING'))
        print('   _args:', getattr(node, '_args', 'MISSING'))
        print('   _kwonlyargs:', getattr(node, '_kwonlyargs', 'MISSING'))
        print('   _kw_defaults:', getattr(node, '_kw_defaults', 'MISSING'))
        print('   _defaults:', getattr(node, '_defaults', 'MISSING'))
        args_dict = {
            'args': node.args if node.args else [],
            'vararg': getattr(node, '_vararg', None),
            'kwarg': getattr(node, '_kwarg', None),
            'defaults': getattr(node, '_defaults', []),
            'kwonlyargs': getattr(node, '_kwonlyargs', []),
            'kw_defaults': getattr(node, '_kw_defaults', [])
        }
        print('   args_dict:', json.dumps(args_dict, default=str))
    return orig_gfd(self, node)
CFGCodeGenerator._generate_function_def = traced_gfd

source = code_gen.generate(py_ast)
print('\n6. Final source (user_print region):')
in_up = False
for line in source.split('\n'):
    if 'user_print' in line and 'def ' in line:
        in_up = True
    if in_up:
        print('   ', line)
        if in_up and line.startswith('def '):
            print('   ...')
            break
