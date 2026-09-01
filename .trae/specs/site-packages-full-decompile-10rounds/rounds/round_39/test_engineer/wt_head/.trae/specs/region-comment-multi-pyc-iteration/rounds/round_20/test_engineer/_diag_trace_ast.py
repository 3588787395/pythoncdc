"""R20 diag: trace final AST dict + ast_converter + code_generator for user_print."""
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

cfg_mod = build_cfg(code)
gen_mod = RegionASTGenerator(cfg_mod, top_level_code=code if code.co_name == '<module>' else None)
ast_dict = gen_mod.generate()

# Find user_print in the body
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
print('=== user_print AST dict ===')
print(json.dumps(up_node, indent=2, default=str))

# Now convert to py_ast
from core.cfg.ast_converter import CFGASTConverter
converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)

# Find user_print FunctionDef in py_ast
import ast as pyast
for node in pyast.walk(py_ast):
    if isinstance(node, pyast.FunctionDef) and node.name == 'user_print':
        print('\n=== user_print py_ast FunctionDef.args ===')
        print('  args:', [a.arg for a in node.args.args])
        print('  posonlyargs:', [a.arg for a in node.args.posonlyargs])
        print('  vararg:', node.args.vararg.arg if node.args.vararg else None)
        print('  kwonlyargs:', [a.arg for a in node.args.kwonlyargs])
        print('  kwarg:', node.args.kwarg.arg if node.args.kwarg else None)
        print('  defaults:', [ast.dump(d) for d in node.args.defaults])
        print('  kw_defaults:', [ast.dump(d) if d else None for d in node.args.kw_defaults])
        break

# Now generate source
from core.cfg.code_generator import CFGCodeGenerator
code_gen = CFGCodeGenerator()
source = code_gen.generate(py_ast)
print('\n=== user_print in final source ===')
in_up = False
for line in source.split('\n'):
    if line.startswith('def user_print'):
        in_up = True
    if in_up:
        print(line)
        if line.strip() and not line.startswith(' ') and not line.startswith('def'):
            break
