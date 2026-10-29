# Probe2: inspect FunctionDef node args after _build_function_def returns.
import sys, os
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
os.chdir(r'D:\temp\opencode')

from core.cfg import region_ast_generator as rag

orig_bfd = rag.RegionASTGenerator._build_function_def

def patched(self, func_name=None, body=None, func_obj=None, decorator=None):
    node = orig_bfd(self, func_name=func_name, body=body, func_obj=func_obj, decorator=decorator)
    if isinstance(node, dict) and node.get('type') in ('FunctionDef', 'AsyncFunctionDef'):
        a = node.get('args')
        if isinstance(a, dict):
            _va = a.get('vararg')
            _ka = a.get('kwarg')
            print('[P2] %s vararg=%r kwarg=%r' % (node.get('name'), _va, _ka), file=sys.stderr)
    return node

rag.RegionASTGenerator._build_function_def = patched

import importlib.util
spec = importlib.util.spec_from_file_location('pycdc_main', r'F:\Downloads\pythoncdc-main\pycdc.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['pycdc_main'] = mod
spec.loader.exec_module(mod)
out = mod.decompile_pyc('ann_repro.pyc')
open('ann_repro_probe2.py', 'w', encoding='utf-8').write(out)
print('WROTE', file=sys.stderr)
