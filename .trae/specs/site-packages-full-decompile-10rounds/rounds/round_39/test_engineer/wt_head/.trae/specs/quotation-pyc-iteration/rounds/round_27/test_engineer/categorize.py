"""R27 测试工程师：分类失败函数的字节码差异类型"""
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


def get_instr_list(co):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname == 'EXTENDED_ARG':
            continue
        if ins.opname == 'CACHE':
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def categorize_diff(name, pc, sc):
    """分析单个函数的差异类型，返回分类标签和详细差异"""
    pi = get_instr_list(pc)
    si = get_instr_list(sc)
    diffs = []
    # 找出第一个差异点
    min_len = min(len(pi), len(si))
    first_diff_idx = None
    for i in range(min_len):
        a, b = pi[i], si[i]
        if a[1] != b[1]:
            first_diff_idx = i
            diffs.append(('opname_diff', i, a, b))
            break
        if a[2] != b[2]:
            first_diff_idx = i
            # 判断是跳转目标差异还是常量差异
            if 'JUMP' in a[1] or a[1].startswith('POP_JUMP') or a[1].startswith('FOR_ITER'):
                diffs.append(('jump_target_diff', i, a, b))
            elif a[1] in ('LOAD_CONST', 'LOAD_FAST', 'LOAD_GLOBAL', 'STORE_FAST', 'STORE_NAME'):
                diffs.append(('argval_diff', i, a, b))
            else:
                diffs.append(('argval_diff', i, a, b))
            break
    if first_diff_idx is None and len(pi) != len(si):
        diffs.append(('length_diff', min_len, (len(pi), len(si)), None))
    # 统计所有差异
    total_diffs = 0
    for i in range(min_len):
        if pi[i][1] != si[i][1] or pi[i][2] != si[i][2]:
            total_diffs += 1
    if len(pi) != len(si):
        total_diffs += abs(len(pi) - len(si))
    return diffs, total_diffs, len(pi), len(si)


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    with open('/tmp/r27_failures.txt', 'r', encoding='utf-8') as f:
        failures = [line.strip() for line in f if line.strip()]

    print(f"=== R27 失败函数分类 (共 {len(failures)} 个) ===\n")
    print(f"{'函数名':<35} {'类型':<20} {'差异总数':<10} {'PYC指令数':<12} {'SRC指令数':<12}")
    print("-" * 95)

    categories = {}
    for name in failures:
        pc = pyc_codes[name]
        sc = src_codes[name]
        diffs, total, p_len, s_len = categorize_diff(name, pc, sc)
        cat = diffs[0][0] if diffs else 'unknown'
        categories.setdefault(cat, []).append(name)
        diff_detail = f"{cat}"
        if diffs:
            d = diffs[0]
            if d[0] == 'jump_target_diff':
                a, b = d[2], d[3]
                delta = (b[0] - a[0]) if isinstance(b[0], int) and isinstance(a[0], int) else 0
                diff_detail = f"jump_target(idx={d[1]},{a[1]},{a[2]}→{b[2]})"
            elif d[0] == 'opname_diff':
                a, b = d[2], d[3]
                diff_detail = f"opname(idx={d[1]},{a[1]}→{b[1]})"
            elif d[0] == 'argval_diff':
                a, b = d[2], d[3]
                diff_detail = f"argval(idx={d[1]},{a[1]},{a[2]}→{b[2]})"
            elif d[0] == 'length_diff':
                diff_detail = f"length(p={d[2]},s={d[3]})"
        print(f"{name:<35} {diff_detail[:50]:<50} {total:<10} {p_len:<12} {s_len:<12}")

    print(f"\n=== 分类汇总 ===")
    for cat, names in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"  {cat}: {len(names)} 个")
        for n in names:
            print(f"    - {n}")


if __name__ == '__main__':
    main()
