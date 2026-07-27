"""R23-N9 测试工程师：分类失败函数，找出最小复现模式"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r23_decompiled.py'


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


def first_diff(pi, si):
    """Find first differing instruction index."""
    for i in range(min(len(pi), len(si))):
        a = pi[i]
        b = si[i]
        if a[1] != b[1]:
            return i, 'opname', a, b
        av_a, av_b = a[2], b[2]
        if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
            continue  # treat as equal at this level
        if av_a != av_b:
            return i, 'argval', a, b
    if len(pi) != len(si):
        return min(len(pi), len(si)), 'length', None, None
    return None, None, None, None


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    with open('/tmp/r23_failures.txt') as f:
        failures = [line.strip() for line in f if line.strip()]

    print(f"=== {len(failures)} failures analysis ===\n")
    categories = {}
    for name in failures:
        pc = pyc_codes.get(name)
        sc = src_codes.get(name)
        if not pc or not sc:
            print(f"  {name}: MISSING")
            continue
        pi = get_instr_list(pc)
        si = get_instr_list(sc)
        idx, kind, a, b = first_diff(pi, si)
        if idx is None:
            print(f"  {name}: NO INSTR DIFF (sig only)")
            cat = 'sig_only'
        elif kind == 'length':
            print(f"  {name}: LENGTH diff pyc={len(pi)} src={len(si)}")
            print(f"    First length-diff at idx {idx}")
            ctx_start = max(0, idx - 3)
            print(f"    --- pyc context [{ctx_start}:{min(len(pi), idx+3)}] ---")
            for off, op, av in pi[ctx_start:min(len(pi), idx+3)]:
                print(f"      P: {off:>6} {op:<25} {repr(av)[:60]}")
            print(f"    --- src context [{ctx_start}:{min(len(si), idx+3)}] ---")
            for off, op, av in si[ctx_start:min(len(si), idx+3)]:
                print(f"      S: {off:>6} {op:<25} {repr(av)[:60]}")
            cat = 'length_diff'
        else:
            print(f"  {name}: {kind} diff at idx {idx}")
            print(f"    P: {a[0]:>6} {a[1]:<25} {repr(a[2])[:60]}")
            print(f"    S: {b[0]:>6} {b[1]:<25} {repr(b[2])[:60]}")
            ctx_start = max(0, idx - 3)
            print(f"    --- pyc context [{ctx_start}:{idx+3}] ---")
            for off, op, av in pi[ctx_start:min(len(pi), idx+3)]:
                print(f"      P: {off:>6} {op:<25} {repr(av)[:60]}")
            print(f"    --- src context [{ctx_start}:{idx+3}] ---")
            for off, op, av in si[ctx_start:min(len(si), idx+3)]:
                print(f"      S: {off:>6} {op:<25} {repr(av)[:60]}")
            cat = f"{kind}_diff"
        categories.setdefault(cat, []).append(name)
        print()

    print(f"\n=== Summary ===")
    for cat, names in sorted(categories.items()):
        print(f"  {cat}: {len(names)} - {names[:5]}")


if __name__ == '__main__':
    main()
