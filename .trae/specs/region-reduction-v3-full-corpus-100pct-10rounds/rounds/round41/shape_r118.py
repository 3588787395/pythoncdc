import dis
def sig(c):
    ins=list(dis.get_instructions(c)); line_of={}
    for cl in c.co_lines():
        if cl[2] is not None:
            for o in range(cl[0],cl[1],2): line_of[o]=cl[2]
    su={}
    for i in ins:
        if i.opcode in dis.hasjrel or i.opcode in dis.hasjabs:
            t=i.argval
            if isinstance(t,int): su.setdefault(i.offset,set()).add(t)
    indeg={}
    for o,ts in su.items():
        for t in ts: indeg[t]=indeg.get(t,0)+1
    back=sum(1 for o,ts in su.items() if any(t<=o for t in ts))
    return len(ins),len(su),back,sorted(indeg.values(),reverse=True)
A='''
def f(x, a, b, c, d):
    if x > a and b <= x < c or d == x:
        return 1
    elif x > a and b <= x < c and d >= x >= c:
        return 2
    return 3
'''
B='''
def f(x, a, b, c, d):
    if x > a and b <= x < c or d == x:
        return 1
    elif x > a and b <= x < c:
        if d >= x >= c:
            return 2
    return 3
'''
for nm,src in (('fused',A),('nested',B)):
    co=compile(src,'<t>','exec').co_consts[[i for i,k in enumerate(compile(src,'<t>','exec').co_consts) if hasattr(k,'co_name')][0]]
    for k in compile(src,'<t>','exec').co_consts:
        if getattr(k,'co_name','')=='f': co=k
    print(nm,'instrs jsites back indeg =',sig(co))
