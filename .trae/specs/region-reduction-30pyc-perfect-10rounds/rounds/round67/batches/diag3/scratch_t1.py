# -*- coding: utf-8 -*-
import io, marshal, dis, sys, types
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from difflib import SequenceMatcher
JUMPS=('JUMP','BRANCH','RETURN_GENERATOR')
def load_pyc(path):
    data=io.open(path,'rb').read()
    for off in (16,12,8):
        try: return marshal.loads(data[off:])
        except Exception: pass
def walk(code,out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c,types.CodeType): walk(c,out)
    return out
def instrs(code): return [(i.opname,str(i.argrepr),i.offset) for i in dis.get_instructions(code) if i.opname!='CACHE']
def norm(t):
    op,arg,off=t
    if op.startswith(JUMPS) or arg.startswith('to ') or 'group' in arg: return op+' J'
    if '<code object' in arg: return op+' CODEOBJ'
    return op+' '+arg
pyc=r'F:/Downloads/pythoncdc-main/test_repros/round63_b5/r63b5_w1.pyc'
oc=[c for c in walk(load_pyc(pyc),[]) if c.co_name=='init_connection'][0]
src=io.open('/tmp/hyp.py',encoding='utf-8').read()
tree=compile(src,'hyp','exec')
dc=[c for c in walk(tree,[]) if c.co_name=='init_connection'][0]
A,B=instrs(oc),instrs(dc)
ka,kb=map(norm,A),map(norm,B)
print('orig',len(A),'hyp',len(B))
sm=SequenceMatcher(None,ka,kb,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    print(tag,i1,i2,j1,j2)
    for k in range(i1,i2): print('   O',A[k])
    for k in range(j1,j2): print('   D',B[k])
