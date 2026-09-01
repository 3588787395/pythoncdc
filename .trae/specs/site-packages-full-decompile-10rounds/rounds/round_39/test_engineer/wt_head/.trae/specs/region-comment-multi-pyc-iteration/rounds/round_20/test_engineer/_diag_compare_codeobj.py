"""R20 diag: compare code_obj from to_python_code vs marshal.load for user_print."""
import sys
import types
import marshal

sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

PYC = r'F:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/__init__.pyc'

# Method 1: marshal.load
with open(PYC, 'rb') as f:
    f.read(16)
    code_marshal = marshal.load(f)


def find_co(c, name):
    if c.co_name == name:
        return c
    for k in c.co_consts:
        if hasattr(k, 'co_code'):
            r = find_co(k, name)
            if r is not None:
                return r
    return None


up_marshal = find_co(code_marshal, 'user_print')
print('=== marshal.load user_print ===')
print('co_varnames:', up_marshal.co_varnames)
print('co_argcount:', up_marshal.co_argcount)
print('co_kwonlyargcount:', up_marshal.co_kwonlyargcount)
print('co_flags:', hex(up_marshal.co_flags))


# Method 2: to_python_code (pycdc loader path)
from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(PYC)
# Access module.code directly (load_file doesn't set code_obj)
code_obj = dec.module.code
if hasattr(code_obj, 'get'):
    code_obj = code_obj.get()
if hasattr(code_obj, 'to_python_code'):
    actual_code = code_obj.to_python_code()
else:
    actual_code = code_obj

up_pycdc = find_co(actual_code, 'user_print')
print('\n=== to_python_code user_print ===')
print('co_varnames:', up_pycdc.co_varnames)
print('co_argcount:', up_pycdc.co_argcount)
print('co_kwonlyargcount:', up_pycdc.co_kwonlyargcount)
print('co_flags:', hex(up_pycdc.co_flags))

print('\n=== DIFF ===')
print('varnames match:', up_marshal.co_varnames == up_pycdc.co_varnames)
print('argcount match:', up_marshal.co_argcount == up_pycdc.co_argcount)
print('kwonlyargcount match:', up_marshal.co_kwonlyargcount == up_pycdc.co_kwonlyargcount)
print('flags match:', up_marshal.co_flags == up_pycdc.co_flags)

# Now decompile via pycdc path and check
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator

cfg = build_cfg(actual_code)
gen = RegionASTGenerator(cfg, top_level_code=actual_code if actual_code.co_name == '<module>' else None)
ast_dict = gen.generate()

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

up_node = find_node(ast_dict, 'user_print')
import json
print('\n=== user_print AST dict args (pycdc path) ===')
print(json.dumps(up_node.get('args'), default=str))

converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)
code_gen = CFGCodeGenerator()
source = code_gen.generate(py_ast)
print('\n=== user_print in source (pycdc path) ===')
in_up = False
for line in source.split('\n'):
    if 'def user_print' in line:
        in_up = True
    if in_up:
        print(line)
        if in_up and not line.startswith(' '):
            break
