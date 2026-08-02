"""R20 diag: trace _extract_function_args + _build_function_def for user_print."""
import sys
import types
import marshal

sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

PYC = r'F:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/__init__.pyc'

with open(PYC, 'rb') as f:
    f.read(16)
    code = marshal.load(f)


def find_co(c, name):
    if c.co_name == name:
        return c
    for k in c.co_consts:
        if hasattr(k, 'co_code'):
            r = find_co(k, name)
            if r is not None:
                return r
    return None


up = find_co(code, 'user_print')
print('=== user_print code_obj ===')
print('co_varnames:', up.co_varnames)
print('co_argcount:', up.co_argcount)
print('co_kwonlyargcount:', up.co_kwonlyargcount)
print('co_flags:', hex(up.co_flags))

from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg import build_cfg

# Build a CFG for user_print directly
cfg = build_cfg(up)
gen = RegionASTGenerator(cfg, top_level_code=None)

# Call _extract_function_args directly
args_info = gen._extract_function_args(up)
print('\n=== _extract_function_args(user_print) ===')
import json
print(json.dumps(args_info, indent=2, default=str))

# Now also test the func_obj path: simulate what happens when MAKE_FUNCTION
# produces a FunctionObject with kw_defaults. Check if args_info is correct.
# The bug might be that func_obj path overrides vararg/kwonlyargs.

# Let's also check: does the decompile use recursive path?
# Build the module-level CFG and see how user_print gets decompiled.
print('\n=== Building module CFG and generating ===')
cfg_mod = build_cfg(code)
gen_mod = RegionASTGenerator(cfg_mod, top_level_code=code if code.co_name == '<module>' else None)

# Monkey-patch _build_function_def to trace user_print calls
orig_bfd = RegionASTGenerator._build_function_def
def traced_bfd(self, func_name=None, body=None, func_obj=None, decorator=None):
    if func_name == 'user_print':
        print(f'\n[TRACE] _build_function_def(user_print)')
        print(f'  func_obj is None: {func_obj is None}')
        if func_obj is not None:
            print(f'  func_obj keys: {list(func_obj.keys()) if isinstance(func_obj, dict) else type(func_obj)}')
            if isinstance(func_obj, dict):
                print(f'  func_obj.code: {func_obj.get("code")}')
                print(f'  func_obj.kw_defaults: {func_obj.get("kw_defaults")}')
                print(f'  func_obj.defaults: {func_obj.get("defaults")}')
        # Call original
        result = orig_bfd(self, func_name, body, func_obj, decorator)
        print(f'  result args: {result.get("args") if isinstance(result, dict) else None}')
        return result
    return orig_bfd(self, func_name, body, func_obj, decorator)

RegionASTGenerator._build_function_def = traced_bfd

try:
    ast_dict = gen_mod.generate()
    print('\n[TRACE] generate() done')
except Exception as e:
    import traceback
    traceback.print_exc()
