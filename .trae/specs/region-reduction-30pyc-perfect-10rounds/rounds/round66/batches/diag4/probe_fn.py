import io,sys,marshal,types,dis
sys.stdout.reconfigure(encoding='utf-8')
p=sys.argv[1]; name=sys.argv[2]
data=io.open(p,'rb').read()
code=None
for off in (16,12,8):
    try:
        code=marshal.loads(data[off:]); break
    except Exception: pass
def walk(c,out):
    out.append(c)
    for x in c.co_consts:
        if isinstance(x,types.CodeType): walk(x,out)
    return out
for c in walk(code,[]):
    if c.co_name==name:
        print('firstlineno=%s ninstr=%d'%(c.co_firstlineno,len(list(dis.get_instructions(c)))))
        print('varnames=',c.co_varnames)
        print('names=',c.co_names)
