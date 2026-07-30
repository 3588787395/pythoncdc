"""R25: detailed analysis of one_prod_to_dataframe orig vs new around the divergence."""
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
    print("\n=== ORIG idx 90..160 (offsets ~438-810) ===")
    for i in range(90, min(160, len(oi))):
        x = oi[i]
        sl = x.starts_line or ''
        print(f"  o[{i:>3}] {x.offset:>5} L{str(sl):>5} {x.opname:<26} {x.argrepr}")
    print("\n=== NEW idx 90..160 (offsets ~438-810) ===")
    for i in range(90, min(160, len(ni))):
        x = ni[i]
        sl = x.starts_line or ''
        print(f"  n[{i:>3}] {x.offset:>5} L{str(sl):>5} {x.opname:<26} {x.argrepr}")

    print("\n=== ORIG idx 380..452 (end of loop) ===")
    for i in range(380, len(oi)):
        x = oi[i]
        sl = x.starts_line or ''
        print(f"  o[{i:>3}] {x.offset:>5} L{str(sl):>5} {x.opname:<26} {x.argrepr}")
    print("\n=== NEW idx 380..453 (end of loop) ===")
    for i in range(380, len(ni)):
        x = ni[i]
        sl = x.starts_line or ''
        print(f"  n[{i:>3}] {x.offset:>5} L{str(sl):>5} {x.opname:<26} {x.argrepr}")

if __name__ == '__main__':
    main()
