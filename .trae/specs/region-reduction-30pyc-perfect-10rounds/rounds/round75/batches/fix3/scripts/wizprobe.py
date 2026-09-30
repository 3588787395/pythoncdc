# -*- coding: utf-8 -*-
import importlib.util, io, marshal, os, sys
sys.stdout.reconfigure(encoding='utf-8')
CENTER = r'D:\Temp\opencode\r75gate\center'
arm, pyc, func = sys.argv[1], sys.argv[2], sys.argv[3]
s = importlib.util.spec_from_file_location('h62x', os.path.join(CENTER, 'h62.py'))
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
pycdc = m._load_arm(arm)
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
code = marshal.loads(io.open(pyc,'rb').read()[16:])
def find(c, name):
    for k in c.co_consts:
        if hasattr(k, 'co_code'):
            if k.co_name == name: return k
            r = find(k, name)
            if r: return r
    return None
target = find(code, func) if func != '<module>' else code
cfg = build_cfg(target)
insts=[]; oi=RegionASTGenerator.__init__
def pk(self,*a,**k): oi(self,*a,**k); insts.append(self)
RegionASTGenerator.__init__=pk
gen=RegionASTGenerator(cfg, top_level_code=target); gen.generate()
RegionASTGenerator.__init__=oi
gs=[x for x in insts if getattr(getattr(x,'cfg',None),'code',None) is target]
g=gs[0]
regs=g.regions
def bk(b): return b.start_offset if b else None
for r in regs:
    e=bk(r.entry)
    if e in (0,10,14,18,22,710,714,770):
        print('%s entry=%s type=%s blocks=%s' % (type(r).__name__, e, getattr(getattr(r,'region_type',None),'name',''), sorted(b.start_offset for b in r.blocks)))
        for f in ('condition_block','merge_block'):
            v=getattr(r,f,None)
            if v is not None: print('   %s=%s' % (f,bk(v)))
        for f in ('then_blocks','else_blocks'):
            v=getattr(r,f,None)
            if v is not None: print('   %s=%s' % (f,sorted(b.start_offset for b in v)))
        if getattr(r,'elif_final_else',None) is not None: print('   elif_final_else=%s' % sorted(b.start_offset for b in r.elif_final_else))
for off in (10,22):
    b=cfg.get_block_by_offset(off)
    print('block %d preds=%s succs=%s last=%s' % (off, sorted(p.start_offset for p in b.predecessors), sorted(x.start_offset for x in b.successors), b.get_last_instruction().opname))
