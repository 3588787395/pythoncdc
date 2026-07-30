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
# 找首个 opname 差异（不是 argval 差异）
print("=== 找首个 opname 差异（结构差异源头）===")
for idx in range(max(len(oi),len(ni))):
    a=oi[idx] if idx<len(oi) else None; b=ni[idx] if idx<len(ni) else None
    if a is None: print(f"idx{idx}: new 多出 {b.opname}"); break
    if b is None: print(f"idx{idx}: orig 多出 {a.opname}"); break
    if a.opname!=b.opname:
        print(f"idx{idx} off O={a.offset} N={b.offset}: O={a.opname} {a.argval!r} | N={b.opname} {b.argval!r}")
        lo=max(0,idx-5); hi=min(max(len(oi),len(ni)),idx+8)
        for j in range(lo,hi):
            aa=oi[j] if j<len(oi) else None; bb=ni[j] if j<len(ni) else None
            print(f"  {j} O:{aa.offset if aa else '-'} {aa.opname if aa else '-'} {aa.argval if aa else '-'}")
            print(f"    N:{bb.offset if bb else '-'} {bb.opname if bb else '-'} {bb.argval if bb else '-'}")
        break
else:
    print("无 opname 差异（纯 argval/offset 平移）")
# offset 对齐检查：找首个 offset 不一致的点
print("\n=== 找首个 offset 不一致点 ===")
for idx in range(min(len(oi),len(ni))):
    if oi[idx].offset!=ni[idx].offset:
        print(f"idx{idx}: O off={oi[idx].offset} ({oi[idx].opname}) | N off={ni[idx].offset} ({ni[idx].opname})")
        lo=max(0,idx-3); hi=min(min(len(oi),len(ni)),idx+3)
        for j in range(lo,hi):
            print(f"  {j} O:{oi[j].offset} {oi[j].opname} | N:{ni[j].offset} {ni[j].opname}")
        break
else:
    print("offset 完全一致")
