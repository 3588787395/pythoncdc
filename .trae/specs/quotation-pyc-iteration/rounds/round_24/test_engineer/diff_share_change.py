"""R24: 详细分析share_change的字节码差异"""
import sys
import importlib.util
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


def get_instrs(co):
    return [(ins.offset, ins.opname, ins.argval, getattr(ins, 'argrepr', '')) for ins in dis.get_instructions(co) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]


def show_diff(name, pyc_codes, src_codes, start_offset=None, end_offset=None):
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = get_instrs(pc)
    si = get_instrs(sc)
    print(f"\n=== {name} ===")
    print(f"pyc: {len(pi)} instrs, src: {len(si)} instrs")

    # Find first diff
    first_diff = None
    for i in range(max(len(pi), len(si))):
        a = pi[i] if i < len(pi) else None
        b = si[i] if i < len(si) else None
        if not (a and b and a[1] == b[1] and a[2] == b[2]):
            first_diff = i
            break
    print(f"first_diff: {first_diff}")
    if first_diff is None:
        return

    start = max(0, first_diff - 10)
    end = min(max(len(pi), len(si)), first_diff + 40)
    for i in range(start, end):
        a = pi[i] if i < len(pi) else None
        b = si[i] if i < len(si) else None
        a_str = f"p: {a[0]:4d} {a[1]:30s} {a[3]}" if a else "p: (none)"
        b_str = f"s: {b[0]:4d} {b[1]:30s} {b[3]}" if b else "s: (none)"
        match = "OK" if a and b and a[1] == b[1] and a[2] == b[2] else "!!"
        print(f"  [{i:3d}] {match} {a_str}")
        print(f"         {match} {b_str}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    # Look at share_change - BoolOp pattern
    show_diff('share_change', pyc_codes, src_codes)
    print()
    # Print full pyc bytecode
    print("--- pyc share_change full ---")
    for ins in dis.get_instructions(pyc_codes['share_change']):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        print(f"  {ins.offset:4d} {ins.opname:30s} {getattr(ins, 'argrepr', '')}")
    print()
    print("--- src share_change full ---")
    for ins in dis.get_instructions(src_codes['share_change']):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        print(f"  {ins.offset:4d} {ins.opname:30s} {getattr(ins, 'argrepr', '')}")


if __name__ == '__main__':
    main()
