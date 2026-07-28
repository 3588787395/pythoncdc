"""R27 测试工程师：dump share_change 和 balance_statement 的源码与字节码"""
import sys
import dis
import types
import re

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


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    with open(SRC, 'r', encoding='utf-8') as f:
        src_text = f.read()

    for fn in ['share_change', 'balance_statement']:
        print(f"\n{'='*80}\n=== {fn} 源码（反编译后）===\n{'='*80}")
        m = re.search(rf'def {fn}\([^)]*\)[^\n]*:\n', src_text)
        if m:
            start = m.start()
            lines = src_text[start:].split('\n')
            for i, line in enumerate(lines[:60]):
                print(f"{i+1:>3} {line}")

        print(f"\n=== {fn} PYC 字节码（前120条）===")
        co = pyc_codes[fn]
        count = 0
        for ins in dis.get_instructions(co):
            if ins.opname in ('EXTENDED_ARG', 'CACHE'):
                continue
            print(f"  {ins.offset:>4} {ins.opname:<35} {ins.argrepr}")
            count += 1
            if count >= 120:
                break


if __name__ == '__main__':
    main()
