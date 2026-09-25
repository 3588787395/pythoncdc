import io, marshal, os, sys, types, time
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main'); sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    d=io.open(p,'rb').read()
    for off in (16,12,8):
        try: return marshal.loads(d[off:])
        except Exception: pass
    return None
def walk(c,o):
    o.append(c)
    for k in c.co_consts:
        if isinstance(k,types.CodeType): walk(k,o)
    return o
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator as GC
NOISE={'RESUME','NOP','CACHE','PUSH_NULL','POP_TOP'}
def offs(bs): return [getattr(b,'start_offset',None) for b in (bs or [])]
def stmt_free(bs):
    for b in (bs or []):
        for i in b.instructions:
            if i.opname in NOISE: continue
            if i.opname.startswith(('JUMP','POP_JUMP')): continue
            return False
    return True
hits=[]
orig=GC._merge_block_is_then_exclusive
def w(self, region):
    r=orig(self, region)
    if r:
        mb=region.merge_block
        owner=self.region_analyzer.block_to_region.get(mb)
        hits.append(dict(f=self._cf, fn=self._cn, e=getattr(region.entry,'start_offset',None),
            then=offs(region.then_blocks), elseb=offs(region.else_blocks),
            cc=offs(getattr(region,'chained_compare_blocks',None)),
            merge=getattr(mb,'start_offset',None), rt=region.region_type.name,
            efree=stmt_free(region.else_blocks),
            owner=(type(owner).__name__ if owner is not None else None),
            owner_entry=(getattr(getattr(owner,'entry',None),'start_offset',None) if owner is not None else None),
            mblanks=[getattr(x,'start_offset',None) for x in (getattr(region,'merge_block',None) and []) or []]))
    return r
GC._merge_block_is_then_exclusive=w
R='D:/Temp/opencode/r66gate/diag1/'
files=[l.strip() for l in io.open('D:/Temp/opencode/r65gate/all402.txt',encoding='utf-8') if l.strip()]
ns=int(sys.argv[1]); sh=int(sys.argv[2])
t0=time.time(); done=0
for i,f in enumerate(files):
    if i%ns!=sh: continue
    if time.time()-t0>230: print('STOP-BUDGET at',i); break
    GC._cf=os.path.basename(f); GC._cn=None
    top=load(f)
    if top is None: continue
    for c in walk(top,[]):
        GC._cn=c.co_name
        try:
            cfg=build_cfg(c); g=GC(cfg, top_level_code=c if c.co_name=='<module>' else None); g.generate()
        except Exception: pass
    done+=1
out=R+'dump/ccprobe_%d.jsonl'%sh
with io.open(out,'w',encoding='utf-8') as fh:
    for h in hits: fh.write(json_d:=__import__('json').dumps(h,ensure_ascii=False)+'\n')
print('files=%d hits=%d -> %s'%(done,len(hits),out))
