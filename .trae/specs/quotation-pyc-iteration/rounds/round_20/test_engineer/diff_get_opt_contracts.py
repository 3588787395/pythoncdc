"""R20 测试工程师：详细对比 get_opt_contracts 的字节码差异（LOAD_GLOBAL错误）"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r20_decompiled.py'


def load_pyc_code_objects(pyc_path):
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
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    name = 'get_opt_contracts'
    pc = pyc_codes[name]
    sc = src_codes[name]

    pi = get_instr_list(pc)
    si = get_instr_list(sc)

    print(f"=== {name}: pyc={len(pi)} src={len(si)} ===")
    print(f"pyc co_names: {pc.co_names}")
    print(f"src co_names: {sc.co_names}")
    print()
    max_len = max(len(pi), len(si))
    for i in range(max_len):
        p = pi[i] if i < len(pi) else None
        s = si[i] if i < len(si) else None
        marker = ''
        if p and s:
            if p[1] != s[1] or p[2] != s[2]:
                marker = ' <-- DIFF'
        elif p and not s:
            marker = ' <-- ONLY IN PYC'
        elif s and not p:
            marker = ' <-- ONLY IN SRC'
        if p:
            print(f"  [{i:3d}] P: {p[0]:5d} {p[1]:35s} {p[2]!r}{marker}")
        if s:
            print(f"        S: {s[0]:5d} {s[1]:35s} {s[2]!r}")
        if marker:
            # print surrounding context for diffs
            pass


if __name__ == '__main__':
    main()
