# Fine-grained probe: which helper consumes offsets 82..130 of x1 f,
# and what instruction slices each receives.
import sys, os, traceback
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
os.chdir(r'D:\temp\opencode')

from core.cfg import region_ast_generator as rag

TARGET_LO, TARGET_HI = 80, 132

def mk(name, orig):
    def patched(self, instrs, *a, **kw):
        offs = [getattr(i, 'offset', None) for i in instrs]
        hit = offs and any(o is not None and TARGET_LO <= o <= TARGET_HI for o in offs)
        r = orig(self, instrs, *a, **kw)
        if hit:
            ops = [(i.offset, i.opname) for i in instrs]
            st = traceback.extract_stack()[-3:-1]
            caller = ' <- '.join('%s:%s' % (f.filename.split(chr(92))[-1], f.lineno) for f in st)
            print('[%s] in=%s out=%d caller=%s' % (name, ops, (len(r) if isinstance(r, list) else -1), caller), file=sys.stderr)
        return r
    return patched

rag.RegionASTGenerator._build_statements_from_instructions = mk('BSFI', rag.RegionASTGenerator._build_statements_from_instructions)
rag.RegionASTGenerator._build_statement = mk('BST', rag.RegionASTGenerator._build_statement)
rag.RegionASTGenerator._build_store_statement = mk('BSS', rag.RegionASTGenerator._build_store_statement)

_orig_ret = rag.RegionASTGenerator._generate_return_ast
def pret(self, *a, **kw):
    r = _orig_ret(self, *a, **kw)
    return r
rag.RegionASTGenerator._generate_return_ast = pret

import importlib.util
spec = importlib.util.spec_from_file_location('pycdc_main', r'F:\Downloads\pythoncdc-main\pycdc.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['pycdc_main'] = mod
spec.loader.exec_module(mod)
out = mod.decompile_pyc('x1_tuple_lambda_return.pyc')
