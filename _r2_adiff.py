"""difflib-based aligned diff of raw instruction sequences, orig pyc vs decompiled OK.py.
Usage: python _r2_adiff.py <pyc> <OK.py> <funcname> [context]"""
import marshal, dis, sys, types, py_compile, difflib
def extract(code_obj, result=None):
    if result is None: result = {}
    result.setdefault(code_obj.co_name or '<module>', []).append(code_obj)
    for c in code_obj.co_consts:
        if isinstance(c, types.CodeType): extract(c, result)
    return result
def load(p):
    with open(p,'rb') as f: f.read(16); return marshal.load(f)
pyc, okpy, fname = sys.argv[1], sys.argv[2], sys.argv[3]
ctx = int(sys.argv[4]) if len(sys.argv)>4 else 6
om, dm = extract(load(pyc)), extract(load(py_compile.compile(okpy, doraise=True, quiet=2)))
oc, dc = om[fname][0], dm[fname][0]
def seq(co):
    out=[]
    for i in dis.get_instructions(co):
        a = i.argrepr
        if i.opname in ('EXTENDED_ARG','PRECALL','NOP','RESUME','CACHE'): continue
        if i.opname=='CACHE': continue
        out.append(f"{i.opname} {a}" if a else i.opname)
    return out
o, d = seq(oc), seq(dc)
sm = difflib.SequenceMatcher(None, o, d, autojunk=False)
print(f"== {fname}: orig={len(o)} decomp={len(d)}  ratio={sm.ratio():.3f}")
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal': continue
    print(f"--- {tag}: orig[{i1}:{i2}] decomp[{j1}:{j2}]")
    for k in range(max(0,i1-ctx), min(len(o), i2+ctx)):
        mark = '>>' if i1 <= k < i2 else '  '
        print(f"  O{k:4d}{mark} {o[k]}")
    print('  ' + '-'*50)
    for k in range(max(0,j1-ctx), min(len(d), j2+ctx)):
        mark = '>>' if j1 <= k < j2 else '  '
        print(f"  D{k:4d}{mark} {d[k]}")
