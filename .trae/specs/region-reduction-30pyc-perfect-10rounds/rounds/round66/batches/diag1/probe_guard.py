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
trues=[]
orig=GC._merge_block_is_then_exclusive
def w(self, region):
    r=orig(self, region)
    if r:
        mb=region.merge_block
        jump_to_mb=any((b.get_last_instruction() is not None
                        and b.get_last_instruction().opname.startswith('JUMP')
                        and b.get_last_instruction().argval==mb.start_offset)
                       for b in (region.then_blocks or []))
        trues.append(dict(file=self._cur_file, fn=self._cur_fn, entry=getattr(region.entry,'start_offset',None),
                          then=offs(region.then_blocks), elseb=offs(region.else_blocks),
                          elifc=offs(getattr(region,'elif_conditions',None)),
                          cc=offs(getattr(region,'chained_compare_blocks',None)),
                          merge=getattr(mb,'start_offset',None), jump_to_mb=jump_to_mb,
                          rt=region.region_type.name, cond=getattr(region.condition_block,'start_offset',None)))
    return r
GC._merge_block_is_then_exclusive=w
files=[]
R='D:/Temp/opencode/r66gate/diag1/'
for lf in (R+'targets.txt',R+'battery.txt',R+'canary.txt',R+'synth_r66.txt'):
    files += [l.strip() for l in io.open(lf,encoding='utf-8') if l.strip()]
import time
t0=time.time()
for f in files:
    GC._cur_file=os.path.basename(f); GC._cur_fn=None
    try: top=load(f)
    except Exception as e: print('skip',f,e); continue
    for c in walk(top,[]):
        GC._cur_fn=c.co_name
        try:
            cfg=build_cfg(c); g=GC(cfg, top_level_code=c if c.co_name=='<module>' else None)
            g.generate()
        except Exception: pass
print('elapsed %.1f  W15-C True count=%d'%(time.time()-t0,len(trues)))
for t in trues:
    print('  %-30s %-28s entry=%-5s then=%-8s else=%-8s elif=%-6s cc=%-10s merge=%-5s cond=%-5s rt=%s jump_to_mb=%s'
          % (t['file'],t['fn'],t['entry'],t['then'],t['elseb'],t['elifc'],t['cc'],t['merge'],t['cond'],t['rt'],t['jump_to_mb']))
