import sys, io, traceback
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
import os
os.chdir('F:/Downloads/pythoncdc-main')
from pycdc import PycDecompiler
from core.cfg import region_ast_generator as rag

RAG = rag.RegionASTGenerator

orig_scan = RAG._scan_prefix_chain_assign
def h_scan(self, instrs, store_idx, stmt_instrs):
    out = orig_scan(self, instrs, store_idx, stmt_instrs)
    names = [t.get('id') for t in (out[0].get('targets') if out[0] else [])]
    print('[SCAN] store_idx=%s instr=%s targets=%s -> %s end=%s' % (
        store_idx, instrs[store_idx].opname if 0 <= store_idx < len(instrs) else '?',
        names, 'chain' if out[0] else 'None', out[1]))
    return out
RAG._scan_prefix_chain_assign = h_scan

orig_bss = RAG._build_store_statement
def h_bss(self, instrs, block=None):
    out = orig_bss(self, instrs, block)
    if out and out.get('type') == 'Assign':
        tg = out.get('targets')
        tn = [t.get('id') for t in tg] if isinstance(tg, list) else tg
        if tn and ('a' in tn or 'b' in tn or 'c' in tn):
            ops = [(i.opname, getattr(i,'argval',None) if isinstance(getattr(i,'argval',None), str) else i.offset) for i in (instrs or [])]
            print('[BSS abc] ops:', ops)
            st = ''.join(traceback.format_stack()[-6:-1]).strip().replace(chr(10), ' | ')[-500:]
            print('[BSS abc] stack:', st)
    return out
RAG._build_store_statement = h_bss

d = PycDecompiler()
d.load_file(sys.argv[1])
buf = io.StringIO()
d.decompile(buf, use_region=True)
