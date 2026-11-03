import sys, io
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
import os
os.chdir('F:/Downloads/pythoncdc-main')
from pycdc import PycDecompiler
from core.cfg import region_ast_generator as rag

LOG = open('D:/temp/opencode/cl_layout/r98/mc_log.txt', 'w', encoding='utf-8')
RAG = rag.RegionASTGenerator
orig = RAG._generate_match
def h(self, region):
    guards = getattr(region, 'case_guards', [])
    cb = getattr(region, 'case_bodies', [])
    for i in range(len(cb)):
        g = guards[i] if i < len(guards) else None
        gp = self._collect_guard_pattern_blocks(region, i) if g is not None else set()
        LOG.write('case %d guard=%r\n' % (i, str(g)[:80]))
        for b in cb[i]:
            ops = [j.opname for j in b.instructions]
            LOG.write('   blk@%s in_gp=%s ops=%s\n' % (b.start_offset, b in gp, ops[:14]))
    LOG.write('\n')
    return orig(self, region)
RAG._generate_match = h

d = PycDecompiler()
d.load_file(sys.argv[1])
buf = io.StringIO()
d.decompile(buf, use_region=True)
LOG.write('done\n')
LOG.close()
