"""Disassemble named function(s) from a pyc. Usage: python _r2_dis.py <pyc> <funcname> [ctx_offset]"""
import marshal, dis, sys, types

def extract(code_obj, result=None):
    if result is None: result = {}
    name = code_obj.co_name or '<module>'
    result.setdefault(name, []).append(code_obj)
    for c in code_obj.co_consts:
        if isinstance(c, types.CodeType):
            extract(c, result)
    return result

def main():
    pyc, fname = sys.argv[1], sys.argv[2]
    ctx = int(sys.argv[3]) if len(sys.argv) > 3 else None  # center offset
    with open(pyc, 'rb') as f:
        f.read(16); code = marshal.load(f)
    funcs = extract(code)
    if fname not in funcs:
        print(f"NOT FOUND {fname}; available: {sorted(funcs)[:60]}"); return
    co = funcs[fname][0]
    instrs = list(dis.get_instructions(co))
    lo, hi = 0, len(instrs)
    if ctx is not None:
        # center on instruction whose offset == ctx
        ci = next((i for i,ins in enumerate(instrs) if ins.offset == ctx), None)
        if ci is None:
            ci = next((i for i,ins in enumerate(instrs) if abs(ins.offset-ctx)<4), 0)
        lo, hi = max(0, ci-45), min(len(instrs), ci+45)
        print(f"--- {fname}: showing instr idx {lo}..{hi-1} of {len(instrs)} (offset {ctx}) ---")
    else:
        print(f"--- {fname}: {len(instrs)} instrs ---")
    print(f"consts: {[c for c in co.co_consts if not isinstance(c, types.CodeType)]}")
    print(f"names: {co.co_names}")
    print(f"varnames: {co.co_varnames}")
    for i in range(lo, hi):
        ins = instrs[i]
        tgt = '>>' if ins.is_jump_target else '  '
        print(f"{i:4d} {tgt} {ins.offset:5d} {ins.opname:32s} {ins.argrepr}")

main()
