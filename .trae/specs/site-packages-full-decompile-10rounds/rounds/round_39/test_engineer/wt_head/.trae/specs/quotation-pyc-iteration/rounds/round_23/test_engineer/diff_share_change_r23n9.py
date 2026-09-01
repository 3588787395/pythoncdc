"""R23-N9 调试 share_change 的 jump target 差异"""
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


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    name = 'share_change'
    pc = pyc_codes[name]
    sc = src_codes[name]
    print("=== PYC full instr ===")
    for ins in dis.get_instructions(pc):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        print(f"  P: {ins.offset:>6} {ins.opname:<35} arg={ins.arg} argval={repr(ins.argval)[:60]}")
    print("\n=== SRC full instr ===")
    for ins in dis.get_instructions(sc):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        print(f"  S: {ins.offset:>6} {ins.opname:<35} arg={ins.arg} argval={repr(ins.argval)[:60]}")


if __name__ == '__main__':
    main()
