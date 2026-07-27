"""R23 测试工程师: 分类失败函数的首次差异模式"""
import sys
import importlib.util
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r22_decompiled.py'


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


def first_diff(name, pc, sc):
    pi = get_instr_list(pc)
    si = get_instr_list(sc)
    if len(pi) != len(si):
        return f"length_diff pyc={len(pi)} src={len(si)}"
    for i, (a, b) in enumerate(zip(pi, si)):
        if a[1] != b[1]:
            return f"opname @{a[0]} pyc={a[1]}({a[2]!r}) src={b[1]}({b[2]!r})"
        av_a, av_b = a[2], b[2]
        if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
            if av_a.co_name != av_b.co_name:
                return f"code_obj_name @{a[0]} pyc={av_a.co_name!r} src={av_b.co_name!r}"
            continue
        if av_a != av_b:
            return f"argval @{a[0]} pyc={av_a!r} src={av_b!r} (op={a[1]})"
    return "unknown"


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    common = set(pyc_codes.keys()) & set(src_codes.keys())

    with open('/tmp/r22_failures.txt', 'r', encoding='utf-8') as f:
        failures = [line.strip() for line in f if line.strip()]

    print(f"=== 失败函数 ({len(failures)} 个) 首次差异分类 ===\n")

    categories = {}
    details = []
    for name in failures:
        if name not in common:
            continue
        pc = pyc_codes[name]
        sc = src_codes[name]
        diff = first_diff(name, pc, sc)
        # Categorize
        if diff.startswith('length_diff'):
            cat = 'length_diff'
        elif diff.startswith('opname'):
            cat = 'opname'
        elif diff.startswith('argval'):
            cat = 'argval'
        elif diff.startswith('code_obj_name'):
            cat = 'code_obj'
        else:
            cat = 'unknown'
        categories.setdefault(cat, []).append((name, diff))
        details.append((name, cat, diff))

    for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"--- {cat}: {len(items)} ---")
        for name, diff in items[:8]:
            print(f"  {name}: {diff}")
        if len(items) > 8:
            print(f"  ... ({len(items) - 8} more)")
        print()

    # Save all details
    with open('/tmp/r23_failure_categories.txt', 'w', encoding='utf-8') as f:
        for name, cat, diff in details:
            f.write(f"{cat}\t{name}\t{diff}\n")
    print("详细信息已写入 /tmp/r23_failure_categories.txt")


if __name__ == '__main__':
    main()
