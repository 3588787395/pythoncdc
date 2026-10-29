# Probe3: distinguish the two _build_function_def calls (caller + func_obj state).
import sys, os, traceback
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
os.chdir(r'D:\temp\opencode')

from core.cfg import region_ast_generator as rag

orig_bfd = rag.RegionASTGenerator._build_function_def
N = [0]

def patched(self, func_name=None, body=None, func_obj=None, decorator=None):
    N[0] += 1
    i = N[0]
    has_fo = func_obj is not None
    fo_keys = sorted(func_obj.keys()) if isinstance(func_obj, dict) else None
    # caller stack (2 levels)
    st = traceback.extract_stack()[-4:-1]
    caller = ' <- '.join(f'{f.filename.split(chr(92))[-1]}:{f.lineno}:{f.name}' for f in st)
    node = orig_bfd(self, func_name=func_name, body=body, func_obj=func_obj, decorator=decorator)
    if isinstance(node, dict) and node.get('type') in ('FunctionDef', 'AsyncFunctionDef'):
        a = node.get('args') or {}
        _va = a.get('vararg') if isinstance(a, dict) else None
        _ka = a.get('kwarg') if isinstance(a, dict) else None
        print('[P3#%d] name=%s vararg=%r kwarg=%r fo=%s keys=%s' % (i, node.get('name'), _va, _ka, has_fo, fo_keys), file=sys.stderr)
        print('[P3#%d] caller: %s' % (i, caller), file=sys.stderr)
    return node

rag.RegionASTGenerator._build_function_def = patched

import importlib.util
spec = importlib.util.spec_from_file_location('pycdc_main', r'F:\Downloads\pythoncdc-main\pycdc.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['pycdc_main'] = mod
spec.loader.exec_module(mod)
out = mod.decompile_pyc('ann_repro.pyc')
open('ann_repro_probe3.py', 'w', encoding='utf-8').write(out)
