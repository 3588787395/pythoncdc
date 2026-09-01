"""R17 调试：查看 load_get_index_stocks 函数的反编译结果和原始字节码"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r17_decompiled.py'


def load_pyc_code_objects(pyc_path):
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


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    for fn_name in ['load_get_index_stocks', 'load_get_industry_stocks']:
        print(f"\n{'='*80}\n=== {fn_name} ===\n{'='*80}")

        print("\n--- PYC 字节码 (最后 20 条) ---")
        pc = pyc_codes[fn_name]
        p_instrs = list(dis.get_instructions(pc))
        for ins in p_instrs[-20:]:
            print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")

        print("\n--- SRC 字节码 (最后 20 条) ---")
        sc = src_codes[fn_name]
        s_instrs = list(dis.get_instructions(sc))
        for ins in s_instrs[-20:]:
            print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")

        # 找出在源代码中的位置
        with open(SRC) as f:
            src_lines = f.readlines()
        # 找到 def load_get_index_stocks
        for i, line in enumerate(src_lines):
            if f'def {fn_name}' in line:
                start = i
                # 找到下一个 def 或文件末尾
                end = len(src_lines)
                for j in range(i + 1, len(src_lines)):
                    if src_lines[j].startswith('def ') or src_lines[j].startswith('class '):
                        end = j
                        break
                print(f"\n--- SRC 源码 (行 {start+1}-{end}) ---")
                for k in range(start, end):
                    print(f"  {k+1:4d} {src_lines[k]}", end='')
                break


if __name__ == '__main__':
    main()
