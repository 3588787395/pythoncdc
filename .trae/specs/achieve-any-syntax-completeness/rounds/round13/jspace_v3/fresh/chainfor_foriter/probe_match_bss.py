import sys, io
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
import os
os.chdir('F:/Downloads/pythoncdc-main')
from pycdc import PycDecompiler
from core.cfg import region_ast_generator as rag

LOG = open('D:/temp/opencode/cl_layout/r98/mc2_log.txt', 'w', encoding='utf-8')
RAG = rag.RegionASTGenerator
orig = RAG._generate_block_statements
inmatch = {'depth': 0}
orig_m = RAG._generate_match
def hm(self, region):
    inmatch['depth'] += 1
    try:
        return orig_m(self, region)
    finally:
        inmatch['depth'] -= 1
RAG._generate_match = hm
def h(self, block, *a, **k):
    out = orig(self, block, *a, **k)
    if inmatch['depth'] > 0:
        ops = [i.opname for i in block.instructions][:12]
        LOG.write('[in-match BSS] blk@%s ops=%s -> %d stmts %s\n' % (
            block.start_offset, ops, len(out or []), [s.get('type') for s in (out or [])][:6]))
    return out
RAG._generate_block_statements = h

d = PycDecompiler()
d.load_file(sys.argv[1])
buf = io.StringIO()
d.decompile(buf, use_region=True)
LOG.write('done\n')
LOG.close()
