"""R17 分析 const_diff:LOAD_CONST 失败模式 - 是否为 lambda 假阳性"""
import sys
import importlib.util
import dis
import types
from collections import Counter

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r17_decompiled.py'


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
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    with open('/tmp/r17_failures.txt') as f:
        failures = [l.strip() for l in f if l.strip()]

    # 找出所有 const_diff 的函数
    const_diff_fns = []
    for name in failures:
        pc = pyc_codes.get(name)
        sc = src_codes.get(name)
        if not pc or not sc:
            continue
        pi = get_instr_list(pc)
        si = get_instr_list(sc)
        for i, (a, b) in enumerate(zip(pi, si)):
            if a[1] != b[1]:
                # opname diff
                break
            if a[2] != b[2]:
                # argval diff
                if a[1] == 'LOAD_CONST' and isinstance(a[2], types.CodeType) and isinstance(b[2], types.CodeType):
                    # 检查 lambda code object 是否相同
                    if a[2].co_name == b[2].co_name:
                        # 比较内部字节码
                        p_inner = get_instr_list(a[2])
                        s_inner = get_instr_list(b[2])
                        if p_inner == s_inner:
                            const_diff_fns.append((name, 'lambda_match', a[2].co_name, i))
                        else:
                            const_diff_fns.append((name, 'lambda_diff', a[2].co_name, i))
                            # 显示差异
                            for j, (x, y) in enumerate(zip(p_inner, s_inner)):
                                if x != y:
                                    print(f"  {name} lambda {a[2].co_name} inner diff at {j}: pyc={x}, src={y}")
                                    break
                    else:
                        const_diff_fns.append((name, 'diff_name', f"{a[2].co_name} vs {b[2].co_name}", i))
                break

    print(f"=== const_diff 分析 ({len(const_diff_fns)} 个) ===")
    for name, kind, info, idx in const_diff_fns:
        print(f"  {name}: {kind} ({info}) at idx={idx}")


if __name__ == '__main__':
    main()
