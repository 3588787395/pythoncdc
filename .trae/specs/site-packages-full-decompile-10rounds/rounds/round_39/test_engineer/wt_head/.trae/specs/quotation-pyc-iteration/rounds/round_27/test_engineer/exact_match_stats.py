"""R27 测试工程师：统计字节码一致性（精确匹配 + 指令匹配）"""
import sys
import importlib.util
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r27_decompiled.py'


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


def instrs_equal(pi, si):
    if len(pi) != len(si):
        return False
    for a, b in zip(pi, si):
        if not instr_equal(a, b):
            return False
    return True


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    common = set(pyc_codes.keys()) & set(src_codes.keys())

    exact_match = []
    instr_match = []
    instr_diff = []
    pyc_only = set(pyc_codes.keys()) - set(src_codes.keys())
    src_only = set(src_codes.keys()) - set(pyc_codes.keys())

    for name in sorted(common):
        pc = pyc_codes[name]
        sc = src_codes[name]
        p_instrs = get_instr_list(pc)
        s_instrs = get_instr_list(sc)
        sig_match = (
            pc.co_argcount == sc.co_argcount
            and pc.co_kwonlyargcount == sc.co_kwonlyargcount
            and pc.co_posonlyargcount == sc.co_posonlyargcount
            and pc.co_flags == sc.co_flags
            and pc.co_varnames == sc.co_varnames
            and pc.co_freevars == sc.co_freevars
            and pc.co_cellvars == sc.co_cellvars
            and pc.co_names == sc.co_names
        )
        if instrs_equal(p_instrs, s_instrs) and sig_match:
            exact_match.append(name)
        elif instrs_equal(p_instrs, s_instrs):
            instr_match.append(name)
        else:
            instr_diff.append(name)

    total = len(common)
    print(f"=== 字节码一致性统计 ===")
    print(f"common functions: {total}")
    print(f"pyc-only: {len(pyc_only)}, src-only: {len(src_only)}")
    print(f"精确匹配 (instr+sig): {len(exact_match)} ({100.0*len(exact_match)/total:.1f}%)")
    print(f"指令匹配 (仅 instr): {len(instr_match)} ({100.0*len(instr_match)/total:.1f}%)")
    print(f"指令匹配 (instr-only + exact): {len(exact_match)+len(instr_match)} ({100.0*(len(exact_match)+len(instr_match))/total:.1f}%)")
    print(f"指令差异: {len(instr_diff)} ({100.0*len(instr_diff)/total:.1f}%)")

    if pyc_only:
        print(f"\npyc-only (前10): {sorted(pyc_only)[:10]}")
    if src_only:
        print(f"\nsrc-only (前10): {sorted(src_only)[:10]}")

    print(f"\n=== 失败函数列表 (前40) ===")
    for n in instr_diff[:40]:
        print(f"  {n}")

    with open('/tmp/r27_failures.txt', 'w', encoding='utf-8') as f:
        for n in instr_diff:
            f.write(n + '\n')
    print(f"\n失败列表已写入 /tmp/r27_failures.txt (共 {len(instr_diff)} 个)")


if __name__ == '__main__':
    main()
