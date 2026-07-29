"""R23-N9 找出 <module> 的真正差异（使用 instr_equal 逻辑）"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r23_decompiled.py'


def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(pyc_path)
    if not module:
        return {}
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    result = {}
    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)
    walk(code_obj)
    return result


def load_src_code_objects(src_path):
    with open(src_path, 'r', encoding='utf-8') as f:
        src = f.read()
    code_obj = compile(src, '<decompiled>', 'exec')
    result = {}
    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)
    walk(code_obj)
    return result


def get_instr_list(co):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname == 'EXTENDED_ARG':
            continue
        if ins.opname == 'CACHE':
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def instr_equal(a, b):
    if a[1] != b[1]:
        return False
    av_a, av_b = a[2], b[2]
    if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
        ia = get_instr_list(av_a)
        ib = get_instr_list(av_b)
        if len(ia) != len(ib):
            return False
        for x, y in zip(ia, ib):
            if not instr_equal(x, y):
                return False
        if av_a.co_name != av_b.co_name:
            return False
        if av_a.co_varnames != av_b.co_varnames:
            return False
        if av_a.co_freevars != av_b.co_freevars:
            return False
        if av_a.co_cellvars != av_b.co_cellvars:
            return False
        if av_a.co_argcount != av_b.co_argcount:
            return False
        if av_a.co_kwonlyargcount != av_b.co_kwonlyargcount:
            return False
        if av_a.co_flags != av_b.co_flags:
            return False
        return True
    return av_a == av_b


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    name = '<module>'
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = get_instr_list(pc)
    si = get_instr_list(sc)
    print(f"<module>: pyc={len(pi)} instrs, src={len(si)} instrs")
    for i in range(min(len(pi), len(si))):
        if not instr_equal(pi[i], si[i]):
            print(f"\nFirst real diff at idx {i}:")
            ctx_start = max(0, i - 3)
            ctx_end = min(len(pi), i + 8)
            print(f"--- PYC context [{ctx_start}:{ctx_end}] ---")
            for j in range(ctx_start, ctx_end):
                p = pi[j]
                marker = ">>>" if j == i else "   "
                av_repr = repr(p[2])[:50]
                if isinstance(p[2], types.CodeType):
                    av_repr = f"<code {p[2].co_name}>"
                print(f"  {marker} P: {p[0]:>6} {p[1]:<35} {av_repr}")
            print(f"--- SRC context [{ctx_start}:{min(len(si), ctx_end)}] ---")
            for j in range(ctx_start, min(len(si), ctx_end)):
                s = si[j]
                marker = ">>>" if j == i else "   "
                av_repr = repr(s[2])[:50]
                if isinstance(s[2], types.CodeType):
                    av_repr = f"<code {s[2].co_name}>"
                print(f"  {marker} S: {s[0]:>6} {s[1]:<35} {av_repr}")
            # Check if it's a code object mismatch
            if isinstance(pi[i][2], types.CodeType) and isinstance(si[i][2], types.CodeType):
                print(f"\n  Code object mismatch!")
                print(f"  P code name: {pi[i][2].co_name}")
                print(f"  S code name: {si[i][2].co_name}")
                pia = get_instr_list(pi[i][2])
                sia = get_instr_list(si[i][2])
                print(f"  P code instrs: {len(pia)}, S code instrs: {len(sia)}")
                # Find first diff in the code object
                for k in range(min(len(pia), len(sia))):
                    if not instr_equal(pia[k], sia[k]):
                        print(f"  First diff in code at idx {k}:")
                        print(f"    P: {pia[k][0]:>6} {pia[k][1]:<25} {repr(pia[k][2])[:50]}")
                        print(f"    S: {sia[k][0]:>6} {sia[k][1]:<25} {repr(sia[k][2])[:50]}")
                        break
            break
    else:
        if len(pi) != len(si):
            print(f"\nLength diff at idx {min(len(pi), len(si))}: pyc={len(pi)} src={len(si)}")
        else:
            print("No diff found - sig only")


if __name__ == '__main__':
    main()
