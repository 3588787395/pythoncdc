import sys, io, traceback
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
import os
os.chdir('F:/Downloads/pythoncdc-main')
from pycdc import PycDecompiler
from core.cfg import region_ast_generator as rag

RAG = rag.RegionASTGenerator

orig_bss = RAG._build_store_statement
def h_bss(self, instrs, block=None):
    out = orig_bss(self, instrs, block)
    if out and out.get('type') == 'Assign':
        tg = out.get('targets')
        tn = [t.get('id') for t in tg] if isinstance(tg, list) else tg
        if tn and 'first' in tn:
            ops = [(i.opname, getattr(i,'argval',None) if isinstance(getattr(i,'argval',None), str) else i.offset) for i in (instrs or [])]
            print('[BSS first] ops:', ops)
            st = ''.join(traceback.format_stack()[-8:-1]).strip().replace(chr(10), ' | ')[-700:]
            print('[BSS first] stack:', st)
    return out
RAG._build_store_statement = h_bss

d = PycDecompiler()
d.load_file(sys.argv[1])
buf = io.StringIO()
d.decompile(buf, use_region=True)
