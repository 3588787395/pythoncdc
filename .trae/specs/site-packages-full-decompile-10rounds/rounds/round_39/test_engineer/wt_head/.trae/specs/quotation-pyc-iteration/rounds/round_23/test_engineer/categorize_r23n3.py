"""R23-N3 测试工程师：分类失败函数的首次差异模式"""
import sys
import importlib.util
import dis
import types
import os
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
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
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
            return f"opname @{a[0]} pyc={a[1]} src={b[1]}"
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

    failures = []
    for name in sorted(common):
        pc = pyc_codes[name]
        sc = src_codes[name]
        pi = get_instr_list(pc)
        si = get_instr_list(sc)
        if len(pi) != len(si):
            failures.append((name, f"length_diff pyc={len(pi)} src={len(si)}", pc, sc))
            continue
        diff_found = False
        for a, b in zip(pi, si):
            if a[1] != b[1]:
                failures.append((name, f"opname @{a[0]} pyc={a[1]} src={b[1]}", pc, sc))
                diff_found = True
                break
            av_a, av_b = a[2], b[2]
            if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
                if av_a.co_name != av_b.co_name:
                    failures.append((name, f"code_obj_name @{a[0]} pyc={av_a.co_name!r} src={av_b.co_name!r}", pc, sc))
                    diff_found = True
                    break
                continue
            if av_a != av_b:
                failures.append((name, f"argval @{a[0]} pyc={av_a!r} src={av_b!r} (op={a[1]})", pc, sc))
                diff_found = True
                break
        if not diff_found:
            # Check signature
            sig_match = (
                pc.co_argcount == sc.co_argcount
                and pc.co_kwonlyargcount == sc.co_kwonlyargcount
                and pc.co_posonlyargcount == sc.co_posonlyargcount
                and pc.co_flags == sc.co_flags
                and pc.co_varnames == sc.co_varnames
                and pc.co_freevars == sc.co_freevars
                and pc.co_cellvars == sc.co_cellvars
                and pc.co_names == sc.co_names
            )
            if not sig_match:
                failures.append((name, "signature_diff", pc, sc))

    # Categorize
    categories = collections.Counter()
    for name, diff, _, _ in failures:
        if diff.startswith("length_diff"):
            categories["length_diff"] += 1
        elif diff.startswith("opname"):
            categories["opname_diff"] += 1
        elif diff.startswith("argval"):
            categories["argval_diff"] += 1
        elif diff.startswith("code_obj_name"):
            categories["code_obj_name_diff"] += 1
        elif diff.startswith("signature"):
            categories["signature_diff"] += 1
        else:
            categories["unknown"] += 1

    print(f"=== 失败模式分类 (共 {len(failures)} 个) ===")
    for cat, cnt in categories.most_common():
        print(f"  {cat}: {cnt}")

    print(f"\n=== 详细失败列表 ===")
    for name, diff, _, _ in failures:
        print(f"  {name}: {diff}")


if __name__ == '__main__':
    main()
