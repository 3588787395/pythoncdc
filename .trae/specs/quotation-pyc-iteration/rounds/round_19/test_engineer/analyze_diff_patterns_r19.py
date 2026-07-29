"""R19 测试工程师：分析所有失败函数的差异模式"""
import sys
import dis
import types
from collections import Counter

sys.path.insert(0, '/workspace')

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
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    with open('/tmp/r19_failures.txt') as f:
        failures = [line.strip() for line in f if line.strip()]

    print(f"=== 失败函数差异模式分析 (共 {len(failures)} 个) ===\n")

    # 统计第一条差异指令的 opname
    first_diff_opnames = Counter()
    # 统计指令数差异
    length_diffs = Counter()

    for name in failures:
        pc = pyc_codes.get(name)
        sc = src_codes.get(name)
        if not pc or not sc:
            continue
        pi = get_instr_list(pc)
        si = get_instr_list(sc)
        length_diff = len(pi) - len(si)
        length_diffs[length_diff] += 1

        # 找到第一条差异
        min_len = min(len(pi), len(si))
        first_diff = None
        for i in range(min_len):
            a = pi[i]
            b = si[i]
            if a[1] != b[1] or a[2] != b[2]:
                first_diff = (i, a, b)
                break
        if first_diff:
            idx, a, b = first_diff
            pattern = f"pyc:{a[1]} -> src:{b[1]}"
            first_diff_opnames[pattern] += 1
            if first_diff_opnames[pattern] <= 3:  # 只打印前3个示例
                print(f"  {name}: len_diff={length_diff}, first_diff@{idx}: {pattern}")
                print(f"    pyc: {a[1]:30s} {a[2]}")
                print(f"    src: {b[1]:30s} {b[2]}")

    print(f"\n=== 长度差异分布 ===")
    for diff, count in sorted(length_diffs.items()):
        print(f"  diff={diff:+d}: {count} functions")

    print(f"\n=== 第一条差异指令模式 (前15) ===")
    for pattern, count in first_diff_opnames.most_common(15):
        print(f"  {count:3d}x  {pattern}")


if __name__ == '__main__':
    main()
