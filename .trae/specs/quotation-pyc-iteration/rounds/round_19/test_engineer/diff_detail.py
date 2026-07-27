"""R19 测试工程师：比较 api_get 字节码差异"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r19_decompiled.py'


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
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname == 'EXTENDED_ARG':
            continue
        if ins.opname == 'CACHE':
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else 'api_get'
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    pc = pyc_codes.get(target)
    sc = src_codes.get(target)
    if not pc or not sc:
        print(f'Not found: {target}')
        return
    pi = get_instr_list(pc)
    si = get_instr_list(sc)
    print(f'=== {target} bytecode diff ===')
    print(f'pyc: {len(pi)} instrs, src: {len(si)} instrs')
    max_len = max(len(pi), len(si))
    for i in range(max_len):
        a = pi[i] if i < len(pi) else (None, None, None)
        b = si[i] if i < len(si) else (None, None, None)
        marker = '  ' if a == b else '!!'
        if a[1] != b[1] or a[2] != b[2]:
            print(f'{marker} [{i:3d}] pyc: {a[1]:30s} {a[2]}')
            print(f'{marker}       src: {b[1]:30s} {b[2]}')


if __name__ == '__main__':
    main()
