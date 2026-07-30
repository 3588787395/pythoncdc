"""R25: side-by-side diff of one_prod_to_dataframe orig vs new, find first divergence + EXTENDED_ARG diff."""
import sys, types, dis
sys.path.insert(0, '/workspace')
PYC = '/workspace/quotation.pyc'
DECOMPILED = '/tmp/r25_decompiled.py'

def load_orig():
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(PYC)
    co = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(co, 'to_python_code'):
        co = co.to_python_code()
    return co

def walk_code(co, prefix='', sink=None):
    if sink is None:
        sink = {}
    name = '<module>' if (co.co_name == '<module>' and not prefix) else prefix + co.co_name
    sink[name] = co
    sub = '' if name == '<module>' else name + '.'
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            walk_code(const, sub, sink)
    return sink

def find_co(d, name):
    for k, v in d.items():
        if k == name or k.endswith('.' + name):
            return v
    return None

def get_instrs(co):
    return [ins for ins in dis.get_instructions(co) if ins.opname != 'CACHE']

def main():
    co = load_orig()
    cos = walk_code(co)
    oc = find_co(cos, 'one_prod_to_dataframe')
    with open(DECOMPILED) as f:
        src = f.read()
    new_code = compile(src, '<d>', 'exec')
    ncos = walk_code(new_code)
    nc = find_co(ncos, 'one_prod_to_dataframe')
    oi = get_instrs(oc)
    ni = get_instrs(nc)
    print(f"orig instr count (skip CACHE) = {len(oi)}, new = {len(ni)}")
    # count EXTENDED_ARG
    o_ea = sum(1 for i in oi if i.opname == 'EXTENDED_ARG')
    n_ea = sum(1 for i in ni if i.opname == 'EXTENDED_ARG')
    print(f"orig EXTENDED_ARG = {o_ea}, new = {n_ea}")
    # find first divergence
    n = min(len(oi), len(ni))
    first = None
    for i in range(n):
        ox = oi[i]; nx = ni[i]
        osig = (ox.opname, ox.argval)
        nsig = (nx.opname, nx.argval)
        if osig != nsig:
            first = i
            break
    print(f"\nfirst divergence at idx {first}")
    if first is not None:
        lo = max(0, first - 6); hi = min(n, first + 6)
        print(f"\n=== context idx {lo}..{hi} ===")
        print(f"{'idx':>4} {'ORIG':<60} | {'NEW':<60}")
        for i in range(lo, hi):
            o = oi[i] if i < len(oi) else None
            x = ni[i] if i < len(ni) else None
            orep = f"{o.offset:>4} {o.opname:<20} {str(o.argrepr)[:34]}" if o else ''
            nrep = f"{x.offset:>4} {x.opname:<20} {str(x.argrepr)[:34]}" if x else ''
            mark = '>>>' if i == first else '   '
            print(f"{mark} {i:>3} {orep:<60} | {nrep:<60}")
    # Find all EXTENDED_ARG positions in both and show first mismatch in their placement
    print(f"\n=== EXTENDED_ARG positions ===")
    o_ea_pos = [(i, oi[i].offset) for i in range(len(oi)) if oi[i].opname == 'EXTENDED_ARG']
    n_ea_pos = [(i, ni[i].offset) for i in range(len(ni)) if ni[i].opname == 'EXTENDED_ARG']
    print(f"ORIG EA at idx/offset: {o_ea_pos}")
    print(f"NEW  EA at idx/offset: {n_ea_pos}")
    # show the instruction right before the first extra EA in new
    # find the first idx where new has EA but orig (at same idx) doesn't
    print(f"\n=== first idx where EA presence differs ===")
    for i in range(min(len(oi), len(ni))):
        oe = oi[i].opname == 'EXTENDED_ARG'
        ne = ni[i].opname == 'EXTENDED_ARG'
        if oe != ne:
            print(f"idx {i}: orig={oi[i].opname}@{oi[i].offset}  new={ni[i].opname}@{ni[i].offset}")
            # show context
            for j in range(max(0,i-3), min(len(oi), i+4)):
                print(f"   o[{j}] {oi[j].offset:>4} {oi[j].opname:<18} {str(oi[j].argrepr)[:30]}    |    n[{j}] {ni[j].offset:>4} {ni[j].opname:<18} {str(ni[j].argrepr)[:30]}")
            break

if __name__ == '__main__':
    main()
