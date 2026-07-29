"""R23 测试工程师：完整转储失败函数的字节码和源码"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r22_decompiled.py'


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


def full_dump(name, pyc_codes, src_codes):
    if name not in pyc_codes or name not in src_codes:
        print(f"[SKIP] {name} not found")
        return
    pc = pyc_codes[name]
    sc = src_codes[name]
    print(f"\n{'='*70}")
    print(f"=== {name} ===")
    print(f"  PYC instructions:")
    for ins in dis.get_instructions(pc):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        print(f"    {ins.offset:4d}  {ins.opname:35s} {ins.argval!r}")
    print(f"\n  SRC instructions:")
    for ins in dis.get_instructions(sc):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        print(f"    {ins.offset:4d}  {ins.opname:35s} {ins.argval!r}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else 'get_trading_day_by_date'
    full_dump(target, pyc_codes, src_codes)


if __name__ == '__main__':
    main()
