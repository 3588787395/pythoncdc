# Probe: trace block statement generation; find where x1 elif-branch stmts are built.
import sys, os
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
os.chdir(r'D:\temp\opencode')

from core.cfg import region_ast_generator as rag

orig_bs = rag.RegionASTGenerator._build_statements_from_instructions
orig_gb = rag.RegionASTGenerator._generate_block_statements

def p_bs(self, instrs, block=None):
    offs = [getattr(i, 'offset', None) for i in instrs]
    r = orig_bs(self, instrs, block)
    if offs and any(o is not None and 80 <= o <= 132 for o in offs):
        ops = [(i.offset, i.opname, getattr(i, 'argval', None)) for i in instrs]
        print('[BS] offs=%s stmts=%d' % (offs, len(r)), file=sys.stderr)
        for s in r:
            print('    stmt: %s' % ({k: v for k, v in s.items() if k != 'body'},), file=sys.stderr)
    return r

def p_gb(self, block):
    r = orig_gb(self, block)
    bo = getattr(block, 'start_offset', None)
    if bo is not None and 50 <= bo <= 132:
        print('[GB] block start=%s end=%s stmts=%d' % (
            bo, getattr(block, 'end_offset', None), len(r)), file=sys.stderr)
        for s in r:
            print('    gb-stmt: %s' % (s.get('type'),), file=sys.stderr)
    return r

rag.RegionASTGenerator._build_statements_from_instructions = p_bs
rag.RegionASTGenerator._generate_block_statements = p_gb

import importlib.util
spec = importlib.util.spec_from_file_location('pycdc_main', r'F:\Downloads\pythoncdc-main\pycdc.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['pycdc_main'] = mod
spec.loader.exec_module(mod)
out = mod.decompile_pyc('x1_tuple_lambda_return.pyc')
open('x1_probe_out.py', 'w', encoding='utf-8').write(out)
