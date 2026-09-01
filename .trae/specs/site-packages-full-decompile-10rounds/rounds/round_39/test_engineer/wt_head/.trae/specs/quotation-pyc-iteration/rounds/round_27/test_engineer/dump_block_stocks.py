"""R27 测试工程师：完整dump小失败函数的源码和字节码"""
import sys
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


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    # 显示get_block_stocks的源码片段（反编译后）
    with open(SRC, 'r', encoding='utf-8') as f:
        src_text = f.read()
    # 找到get_block_stocks函数
    import re
    for fn in ['get_block_stocks', 'get_option_info']:
        print(f"\n{'='*80}\n=== {fn} 源码（反编译后）===\n{'='*80}")
        m = re.search(rf'def {fn}\([^)]*\)[^\n]*:\n', src_text)
        if m:
            start = m.start()
            # 取后续100行
            lines = src_text[start:].split('\n')
            for i, line in enumerate(lines[:80]):
                print(f"{i+1:>3} {line}")

    # 显示get_block_stocks的字节码（PYC）
    print(f"\n{'='*80}\n=== get_block_stocks PYC 字节码 ===\n{'='*80}")
    for ins in dis.get_instructions(pyc_codes['get_block_stocks']):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        print(f"  {ins.offset:>4} {ins.opname:<35} {ins.argrepr}")


if __name__ == '__main__':
    main()
