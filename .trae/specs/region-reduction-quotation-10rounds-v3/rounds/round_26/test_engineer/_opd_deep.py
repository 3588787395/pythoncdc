import sys, types, dis
sys.path.insert(0, '/workspace')
from core.pyc_loader_v2 import load_pyc_file_v2
m = load_pyc_file_v2('/workspace/quotation.pyc')
co = m.code.get() if hasattr(m.code,'get') else m.code
if hasattr(co,'to_python_code'): co = co.to_python_code()
def find(c,nm):
    for k in c.co_consts:
        if isinstance(k,types.CodeType) and k.co_name==nm: return k
oco=find(co,'one_prod_to_dataframe')
with open('/tmp/r25_decompiled.py') as f: src=f.read()
mod=compile(src,'<d>','exec')
nco=find(mod,'one_prod_to_dataframe')
oi=list(dis.get_instructions(oco)); ni=list(dis.get_instructions(nco))
print(f"one_prod_to_dataframe: orig={len(oi)} new={len(ni)}")
# 完整 diff（忽略 starts_line + code object 元数据）
def norm(i):
    av=i.argval
    if isinstance(av,types.CodeType): av=('CODE',av.co_name)
    return (i.opname,av)
diffs=[]
for idx in range(max(len(oi),len(ni))):
    a=oi[idx] if idx<len(oi) else None; b=ni[idx] if idx<len(ni) else None
    na=norm(a) if a else None; nb=norm(b) if b else None
    if na!=nb: diffs.append((idx,a,b))
print(f"差异总数(忽略starts_line+code元数据): {len(diffs)}")
print(f"\n=== 所有差异（前后2条上下文）===")
for idx,a,b in diffs[:3]:
    print(f"\n--- idx{idx} off={a.offset if a else '?'} ---")
    lo=max(0,idx-2); hi=min(max(len(oi),len(ni)),idx+5)
    for j in range(lo,hi):
        aa=oi[j] if j<len(oi) else None; bb=ni[j] if j<len(ni) else None
        naa=norm(aa) if aa else None; nbb=norm(bb) if bb else None
        mk='!!' if naa!=nbb else '  '
        print(f"  {j}{mk} O:{aa.offset if aa else '-'} {aa.opname if aa else '-'} {aa.argval if aa else '-'}")
        print(f"    {mk} N:{bb.offset if bb else '-'} {bb.opname if bb else '-'} {bb.argval if bb else '-'}")
