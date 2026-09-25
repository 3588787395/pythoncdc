import dis,io,marshal,types,sys
path=sys.argv[1]; name=sys.argv[2]; lo=int(sys.argv[3]); hi=int(sys.argv[4])
src=sys.argv[5] if len(sys.argv)>5 else 'orig'
d=io.open(path,'rb').read()
code=marshal.loads(d[16:])
def walk(c,o):
    o.append(c)
    for k in c.co_consts:
        if isinstance(k,types.CodeType): walk(k,o)
    return o
if src=='orig':
    c=[x for x in walk(code,[]) if x.co_name==name][0]
else:
    ok='build_landed/IQEngine__plugins__plugin_system_trade__trade_live_brokerOK.py'
    c=[x for x in walk(compile(io.open(ok,encoding='utf-8').read(),ok,'exec'),[]) if x.co_name==name][0]
for i in dis.get_instructions(c):
    if i.opname=='CACHE': continue
    if lo<=i.offset<=hi:
        print('%5d %-26s %-38s L%s'%(i.offset,i.opname,str(i.argrepr)[:38],i.starts_line))
