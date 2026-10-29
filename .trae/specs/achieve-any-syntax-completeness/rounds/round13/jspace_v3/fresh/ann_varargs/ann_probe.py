# Probe: trace annotation loop execution in _build_function_def.
import sys, os
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
os.chdir(r'D:\temp\opencode')

from core.cfg import region_ast_generator as rag

orig_bfd = rag.RegionASTGenerator._build_function_def

def patched(self, func_name=None, body=None, func_obj=None, decorator=None):
    if func_obj is not None and isinstance(func_obj, dict):
        code_obj = func_obj.get('code')
        nm = getattr(code_obj, 'co_name', '?')
        has_ann = 'annotations' in func_obj
        print(f'[PROBE] _build_function_def name={nm} has_annotations_key={has_ann}', file=sys.stderr)
        if has_ann:
            ann = func_obj.get('annotations')
            print(f'[PROBE]   annotations type={type(ann).__name__} repr={repr(ann)[:200]}', file=sys.stderr)
        from core.cfg.region_ast_generator import RegionASTGenerator
        code_obj = func_obj.get('code')
        if isinstance(code_obj, dict) and code_obj.get('type') == 'Constant':
            code_obj = code_obj.get('value')
        if isinstance(code_obj, dict) and code_obj.get('type') == 'CodeObject':
            code_obj = code_obj.get('code')
        args = self._extract_function_args(code_obj) if code_obj is not None else {}
        _va = args.get('vararg')
        _ka = args.get('kwarg')
        _names = []
        for a in (args.get('args') or []):
            if isinstance(a, dict):
                _names.append(a.get('arg'))
            else:
                _names.append(a)
        print('[PROBE]   args vararg=%r kwarg=%r args_names=%r' % (_va, _ka, _names), file=sys.stderr)
    return orig_bfd(self, func_name=func_name, body=body, func_obj=func_obj, decorator=decorator)

rag.RegionASTGenerator._build_function_def = patched

import importlib.util
spec = importlib.util.spec_from_file_location('pycdc_main', r'F:\Downloads\pythoncdc-main\pycdc.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['pycdc_main'] = mod
spec.loader.exec_module(mod)
out = mod.decompile_pyc('ann_repro.pyc')
open('ann_repro_probe.py', 'w', encoding='utf-8').write(out)
print('WROTE ann_repro_probe.py', file=sys.stderr)
