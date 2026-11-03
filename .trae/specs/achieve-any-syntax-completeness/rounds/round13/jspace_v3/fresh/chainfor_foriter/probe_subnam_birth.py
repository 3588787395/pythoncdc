import sys, io, traceback
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
import os
os.chdir('F:/Downloads/pythoncdc-main')
from pycdc import PycDecompiler
from core.cfg import region_ast_generator as rag

LOG = open('D:/temp/opencode/cl_layout/r98/dc26_log.txt', 'w', encoding='utf-8')
RAG = rag.RegionASTGenerator

def is_ph(v):
    return isinstance(v, dict) and v.get('type') == 'Name' and v.get('id') == '1'

orig_sa = RAG._build_subscript_assign
cnt = {'sa': 0, 'hit': 0}
def h_sa(self, instrs):
    out = orig_sa(self, instrs)
    cnt['sa'] += 1
    if isinstance(out, dict) and is_ph(out.get('value')):
        cnt['hit'] += 1
        if cnt['hit'] <= 2:
            try:
                lines = ['[SUBSCRIPT-ASSIGN hit] ninstrs=%r' % (len(instrs),)]
                for i in list(instrs)[:30]:
                    lines.append('   off=%r op=%r argrepr=%r arg=%r' % (getattr(i, 'offset', None), getattr(i, 'opname', None), getattr(i, 'argrepr', None), getattr(i, 'arg', None)))
                lines.append(' stack: ' + ''.join(traceback.format_stack()[-5:-1]).replace(chr(10), ' | ')[-320:])
                LOG.write('\n'.join(lines) + '\n\n')
                LOG.flush()
            except Exception as e:
                LOG.write('[probe err] %r\n' % (e,))
    return out
RAG._build_subscript_assign = h_sa

d = PycDecompiler()
d.load_file(sys.argv[1])
buf = io.StringIO()
d.decompile(buf, use_region=True)
LOG.write('done sa=%s hit=%s\n' % (cnt['sa'], cnt['hit']))
LOG.close()
