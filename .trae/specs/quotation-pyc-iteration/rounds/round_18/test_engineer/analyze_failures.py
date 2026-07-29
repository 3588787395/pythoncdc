"""R18 失败模式详细分析（跳过 lambda 假阳性）"""
import sys
import importlib.util
import dis
import types
from collections import Counter

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r18_decompiled.py'


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


def instr_equal(a, b):
    """比较两条指令，对 code object 只比较内部字节码（忽略 filename）"""
    if a[1] != b[1]:  # opname
        return False
    av_a, av_b = a[2], b[2]
    if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
        ia = get_instr_list(av_a)
        ib = get_instr_list(av_b)
        if len(ia) != len(ib):
            return False
        for x, y in zip(ia, ib):
            if not instr_equal(x, y):
                return False
        if av_a.co_name != av_b.co_name:
            return False
        if av_a.co_varnames != av_b.co_varnames:
            return False
        if av_a.co_freevars != av_b.co_freevars:
            return False
        if av_a.co_cellvars != av_b.co_cellvars:
            return False
        if av_a.co_argcount != av_b.co_argcount:
            return False
        if av_a.co_kwonlyargcount != av_b.co_kwonlyargcount:
            return False
        if av_a.co_flags != av_b.co_flags:
            return False
        return True
    return av_a == av_b


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    with open('/tmp/r18_failures.txt') as f:
        failures = [l.strip() for l in f if l.strip()]

    print(f"=== 真实失败模式分析 ({len(failures)} 个失败) ===\n")

    patterns = Counter()
    real_failures = []
    false_positives = []
    detail_records = []  # (name, pattern, first_diff, p_instrs, s_instrs)

    for name in failures:
        pc = pyc_codes.get(name)
        sc = src_codes.get(name)
        if not pc or not sc:
            continue
        pi = get_instr_list(pc)
        si = get_instr_list(sc)

        is_false_positive = True
        first_real_diff = None
        for i, (a, b) in enumerate(zip(pi, si)):
            if not instr_equal(a, b):
                is_false_positive = False
                first_real_diff = (i, a, b)
                break

        if is_false_positive and len(pi) == len(si):
            false_positives.append(name)
            continue

        real_failures.append(name)

        if first_real_diff:
            i, a, b = first_real_diff
            if a[1] != b[1]:
                pattern = f"opname_diff:{a[1]}_vs_{b[1]}"
            elif a[2] != b[2]:
                if isinstance(a[2], types.CodeType):
                    pattern = "const_diff:code_object"
                else:
                    pattern = f"argval_diff:{a[1]}"
            else:
                pattern = "unknown"
        else:
            pattern = f"length_diff(delta={len(si)-len(pi)})"

        patterns[pattern] += 1
        detail_records.append((name, pattern, first_real_diff, pi, si))

    print(f"假阳性（lambda filename 差异）: {len(false_positives)} 个")
    for n in false_positives:
        print(f"  {n}")
    print()
    print(f"真实失败: {len(real_failures)} 个")
    print()
    print("=== 真实失败模式分布 ===")
    for pat, cnt in patterns.most_common():
        print(f"  {cnt:3d}  {pat}")

    print("\n=== 按模式分组的失败函数 ===")
    by_pat = {}
    for n, p, fd, pi, si in detail_records:
        by_pat.setdefault(p, []).append((n, fd, pi, si))
    for p in sorted(by_pat.keys()):
        print(f"\n--- {p} ({len(by_pat[p])} 个) ---")
        for n, fd, pi, si in by_pat[p][:5]:
            if fd:
                i, a, b = fd
                print(f"  {n}: idx={i}, pyc=({a[0]},{a[1]},{a[2]!r}), src=({b[0]},{b[1]},{b[2]!r}), len_p={len(pi)}, len_s={len(si)}")
            else:
                print(f"  {n}: len_p={len(pi)}, len_s={len(si)}")


if __name__ == '__main__':
    main()
