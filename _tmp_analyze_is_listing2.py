import dis, marshal, types
pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQEngine/core/asset.pyc'
with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find(code, name, res=None):
    if res is None:
        res = []
    if code.co_name == name:
        res.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            find(c, name, res)
    return res

listings = find(code, 'is_listing')
for i, co in enumerate(listings):
    instrs = [(j.opname, j.argrepr) for j in dis.get_instructions(co)]
    print(f'is_listing #{i}: {len(instrs)} instrs, co_consts={co.co_consts[:3]}')
    for j, (op, arg) in enumerate(instrs):
        print(f'  [{j:2d}] {op:<30} {arg}')
    print()
