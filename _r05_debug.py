import py_compile, tempfile, os, sys, json
sys.path.insert(0, '.')
import core.cfg.region_ast_generator as m

orig_bfd = m.RegionASTGenerator._build_function_def
def wrap_bfd(self, func_name=None, body=None, func_obj=None, decorator=None):
    sys.stderr.write(f'[DBG _build_function_def] func_name={func_name} func_obj={type(func_obj).__name__} decorator={decorator}\n')
    r = orig_bfd(self, func_name=func_name, body=body, func_obj=func_obj, decorator=decorator)
    sys.stderr.write(f'[DBG _build_function_def] result.decorator_list={r.get("decorator_list")}\n')
    return r
m.RegionASTGenerator._build_function_def = wrap_bfd

orig_ed = m.RegionASTGenerator._extract_decorators
def wrap_ed(self, call_node):
    r = orig_ed(self, call_node)
    sys.stderr.write(f'[DBG _extract_decorators] call_node.type={call_node.get("type") if isinstance(call_node,dict) else type(call_node).__name__} func={call_node.get("func") if isinstance(call_node,dict) else None} -> result={r}\n')
    return r
m.RegionASTGenerator._extract_decorators = wrap_ed

orig_rdc = m.RegionASTGenerator._reconstruct_decorator_chain
def wrap_rdc(self, instrs, idx):
    r = orig_rdc(self, instrs, idx)
    sys.stderr.write(f'[DBG _reconstruct_decorator_chain] make_func_idx={idx} result={r}\n')
    return r
m.RegionASTGenerator._reconstruct_decorator_chain = wrap_rdc

from pycdc import decompile_pyc
td = tempfile.mkdtemp()
p = os.path.join(td, 'r.pyc')
py_compile.compile(r'.trae/specs/region-comment-multi-pyc-iteration/rounds/round_05/test_engineer/minimal_repros/repro_01_deco_call_on_method.py', p, doraise=True, quiet=2)
out = decompile_pyc(p)
sys.stderr.write('=== DECOMPILED ===\n')
sys.stderr.write(out + '\n')
