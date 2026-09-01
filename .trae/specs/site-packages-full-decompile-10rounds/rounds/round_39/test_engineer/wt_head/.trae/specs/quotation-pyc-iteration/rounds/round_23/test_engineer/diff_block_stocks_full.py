"""R23-N24: Detailed diff for get_block_stocks"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r23_decompiled.py'

def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(pyc_path)
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
    return [(ins.offset, ins.opname, ins.argval, ins.argrepr) for ins in dis.get_instructions(co) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]

def show_diff_full(name, pyc_codes, src_codes):
    if name not in pyc_codes or name not in src_codes:
        print(f"{name}: not found")
        return
    pa = get_instr_list(pyc_codes[name])
    sa = get_instr_list(src_codes[name])
    print(f"\n=== {name} (p={len(pa)}, s={len(sa)}) ===")
    max_len = max(len(pa), len(sa))
    for i in range(max_len):
        a = pa[i] if i < len(pa) else None
        b = sa[i] if i < len(sa) else None
        a_str = f"{a[0]:4d} {a[1]:28s} {a[3]}" if a else "(none)"
        b_str = f"{b[0]:4d} {b[1]:28s} {b[3]}" if b else "(none)"
        match = "OK" if a and b and a[1] == b[1] and a[2] == b[2] else "!!"
        print(f"  {match} a: {a_str}")
        print(f"  {match} b: {b_str}")

def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    show_diff_full('get_block_stocks', pyc_codes, src_codes)

if __name__ == '__main__':
    main()
