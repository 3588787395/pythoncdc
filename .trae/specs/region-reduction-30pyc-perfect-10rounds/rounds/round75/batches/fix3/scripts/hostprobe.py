# -*- coding: utf-8 -*-
import importlib.util, io, marshal, os, sys
sys.stdout.reconfigure(encoding='utf-8')
CENTER = r'D:\Temp\opencode\r75gate\center'
arm, pyc, func, e_off, else_off = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
s = importlib.util.spec_from_file_location('h62x', os.path.join(CENTER, 'h62.py'))
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
pycdc = m._load_arm(arm)
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
code = marshal.loads(io.open(pyc,'rb').read()[16:])
# find nested code object
def find(c, name):
    for k in c.co_consts:
        if hasattr(k, 'co_code') and k.co_name == name: return k
        if hasattr(k, 'co_code'):
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
g=[x for x in insts if getattr(getattr(x,'cfg',None),'code',None) is target]
g=g[0] if g else None
eb = cfg.get_block_by_offset(else_off)
regs = g.regions if g else []
hosts = [r for r in regs if eb in r.blocks and not (r.entry and r.entry.start_offset==e_off)]
print('else block %d hosted by other regions: %s' % (else_off, [(type(r).__name__, getattr(getattr(r,'region_type',None),'name',''), r.entry.start_offset if r.entry else None) for r in hosts]))
ir = [r for r in regs if r.entry and r.entry.start_offset==e_off]
for r in ir:
    print('ifregion type=%s blocks=%s' % (getattr(getattr(r,'region_type',None),'name',''), sorted(b.start_offset for b in r.blocks)))
