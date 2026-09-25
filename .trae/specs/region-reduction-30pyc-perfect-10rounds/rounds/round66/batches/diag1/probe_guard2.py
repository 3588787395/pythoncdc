import io, marshal, os, sys, types
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main'); sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    d=io.open(p,'rb').read()
    for off in (16,12,8):
        try: return marshal.loads(d[off:])
        except Exception: pass
    raise SystemExit('bad %s'%p)
def walk(c,o):
    o.append(c)
    for k in c.co_consts:
        if isinstance(k,types.CodeType): walk(k,o)
    return o
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator as GC
def offs(bs): return [getattr(b,'start_offset',None) for b in (bs or [])]
NOISE={'RESUME','NOP','CACHE','PUSH_NULL','POP_TOP'}
def arm_stmt_free(bs):
    for b in (bs or []):
        for i in b.instructions:
            if i.opname in NOISE: continue
            if i.opname.startswith(('JUMP','POP_JUMP')): continue
            return False
    return True
trues=[]
orig=GC._merge_block_is_then_exclusive
def w(self, region):
    r=orig(self, region)
    if r:
        efree=arm_stmt_free(region.else_blocks)
        trues.append((self._cur_file,self._cur_fn,offs(region.then_blocks),offs(region.else_blocks),
                      getattr(region.merge_block,'start_offset',None), efree))
    return r
GC._merge_block_is_then_exclusive=w
R='D:/Temp/opencode/r66gate/diag1/'
files=[]
for lf in (R+'targets.txt',R+'battery.txt',R+'canary.txt',R+'synth_r66.txt'):
    files += [l.strip() for l in io.open(lf,encoding='utf-8') if l.strip()]
import time; t0=time.time()
for f in files:
    GC._cur_file=os.path.basename(f); GC._cur_fn=None
    try: top=load(f)
    except Exception as e: print('skip',f,e); continue
    for c in walk(top,[]):
        GC._cur_fn=c.co_name
        try:
            cfg=build_cfg(c); g=GC(cfg, top_level_code=c if c.co_name=='<module>' else None); g.generate()
        except Exception: pass
print('elapsed %.1f W15-C True=%d  would-be-flipped=%d'%(time.time()-t0,len(trues),sum(1 for t in trues if not t[5])))
for t in trues: print('  %-30s %-26s then=%-8s else=%-8s merge=%-5s else_stmt_free=%s'%t)
