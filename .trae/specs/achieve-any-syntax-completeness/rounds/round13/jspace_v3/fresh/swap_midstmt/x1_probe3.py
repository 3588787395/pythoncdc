# Probe3: trace expr_reconstructor.reconstruct + stmt boundary loop inputs for x1.
import sys, os, traceback
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
os.chdir(r'D:\temp\opencode')

from core.cfg import region_ast_generator as rag
from core.cfg.ast_generator_v2 import ExpressionReconstructor as cls

TARGET_LO, TARGET_HI = 80, 132

orig_rec = cls.reconstruct

def prec(self, instrs, *a, **kw):
    offs = [getattr(i, 'offset', None) for i in instrs]
    hit = offs and any(o is not None and TARGET_LO <= o <= TARGET_HI for o in offs)
    r = orig_rec(self, instrs, *a, **kw)
    if hit:
        ops = [(i.offset, i.opname) for i in instrs]
        st = traceback.extract_stack()[-3:-1]
        caller = ' <- '.join('%s:%s' % (f.filename.split(chr(92))[-1], f.lineno) for f in st)
        print('[REC] in=%s out=%s caller=%s' % (ops, (r.get('type') if isinstance(r, dict) else type(r).__name__), caller), file=sys.stderr)
    return r

cls.reconstruct = prec

import importlib.util
spec = importlib.util.spec_from_file_location('pycdc_main', r'F:\Downloads\pythoncdc-main\pycdc.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['pycdc_main'] = mod
spec.loader.exec_module(mod)
out = mod.decompile_pyc('x1_tuple_lambda_return.pyc')
