"""R23-N4: 分类失败函数的失败模式，找出共性"""
import sys
import dis
import types
import collections

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
    """返回 (offset, opname, argval) 列表"""
    out = []
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        out.append((ins.offset, ins.opname, ins.argval))
    return out


def first_diff_detail(name, pc, sc):
    """返回首个差异详情"""
    pi = get_instr_list(pc)
    si = get_instr_list(sc)
    if len(pi) != len(si):
        # 找首个 opname 差异或长度差异
        for i in range(min(len(pi), len(si))):
            if pi[i][1] != si[i][1]:
                return ("opname_diff", i, pi[i], si[i])
        return ("length_diff", min(len(pi), len(si)),
                pi[min(len(pi), len(si))-1] if pi else None,
                si[min(len(pi), len(si))-1] if si else None)
    for i, (a, b) in enumerate(zip(pi, si)):
        if a[1] != b[1]:
            return ("opname_diff", i, a, b)
        av_a, av_b = a[2], b[2]
        if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
            if av_a.co_name != av_b.co_name:
                return ("code_obj_name_diff", i, a, b)
            continue
        if av_a != av_b:
            return ("argval_diff", i, a, b)
    return None


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    common = set(pyc_codes.keys()) & set(src_codes.keys())

    failures = []
    for name in sorted(common):
        pc = pyc_codes[name]
        sc = src_codes[name]
        pi = get_instr_list(pc)
        si = get_instr_list(sc)
        if pi == si:
            continue
        detail = first_diff_detail(name, pc, sc)
        failures.append((name, detail, pi, si))

    print(f"=== R23-N3 失败函数分类 ===")
    print(f"总失败: {len(failures)}")

    # 分类
    categories = collections.Counter()
    for name, d, _, _ in failures:
        if d is None:
            categories["unknown"] += 1
        else:
            categories[d[0]] += 1

    print("\n--- 分类统计 ---")
    for cat, cnt in categories.most_common():
        print(f"  {cat}: {cnt}")

    # 按分类列出
    print("\n--- 详细列表 ---")
    for cat, _ in categories.most_common():
        print(f"\n## {cat}")
        for name, d, pi, si in failures:
            if d is None:
                if cat == "unknown":
                    print(f"  {name}: unknown")
                continue
            if d[0] != cat:
                continue
            if cat == "length_diff":
                print(f"  {name}: pyc={len(pi)} src={len(si)} (diff={len(si)-len(pi)})")
            elif cat == "opname_diff":
                _, i, a, b = d
                print(f"  {name}: @{a[0]} pyc={a[1]}({a[2]!r}) src={b[1]}({b[2]!r}) [pyc_i={i}]")
            elif cat == "argval_diff":
                _, i, a, b = d
                print(f"  {name}: @{a[0]} op={a[1]} pyc={a[2]!r} src={b[2]!r} [pyc_i={i}]")
            elif cat == "code_obj_name_diff":
                _, i, a, b = d
                print(f"  {name}: @{a[0]} pyc={a[2].co_name!r} src={b[2].co_name!r}")


if __name__ == '__main__':
    main()
