"""R25: dump one_prod_to_dataframe orig full bytecode with offsets + lines for elif chain analysis."""
import sys, types, dis
sys.path.insert(0, '/workspace')
PYC = '/workspace/quotation.pyc'

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

def main():
    co = load_orig()
    cos = walk_code(co)
    oc = find_co(cos, 'one_prod_to_dataframe')
    instrs = [ins for ins in dis.get_instructions(oc) if ins.opname != 'CACHE']
    # Show all POP_JUMP and JUMP_FORWARD instructions and their targets, with context
    print("=== All JUMP/FOR_ITER instructions in ORIG one_prod_to_dataframe ===")
    for i, ins in enumerate(instrs):
        if 'JUMP' in ins.opname or ins.opname == 'FOR_ITER':
            print(f"  idx[{i:>3}] off {ins.offset:>5} L{str(ins.starts_line or ''):>5} {ins.opname:<26} {ins.argrepr}")
    print("\n=== ORIG offsets 620-820 (the if/elif chain region) ===")
    for i, ins in enumerate(instrs):
        if 620 <= ins.offset <= 820:
            sl = ins.starts_line or ''
            print(f"  o[{i:>3}] {ins.offset:>5} L{str(sl):>5} {ins.opname:<26} {ins.argrepr}")
    # Show what's at offset ~800 and ~1630-1650 (loop end)
    print("\n=== ORIG offsets 1620-1660 (loop end region) ===")
    for i, ins in enumerate(instrs):
        if 1620 <= ins.offset <= 1660:
            sl = ins.starts_line or ''
            print(f"  o[{i:>3}] {ins.offset:>5} L{str(sl):>5} {ins.opname:<26} {ins.argrepr}")

if __name__ == '__main__':
    main()
