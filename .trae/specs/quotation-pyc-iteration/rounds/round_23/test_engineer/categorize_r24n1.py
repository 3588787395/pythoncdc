"""R24-N1 测试工程师：详细分类21个失败函数的字节码差异类型"""
import sys
import importlib.util
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


def get_instrs(co):
    return [(ins.offset, ins.opname, ins.argval, ins.argrepr) for ins in dis.get_instructions(co) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]


pyc_codes = load_pyc_code_objects(PYC)
src_codes = load_src_code_objects(SRC)

with open('/tmp/r23_failures.txt', 'r') as f:
    failures = [l.strip() for l in f if l.strip()]

print(f"Total failures: {len(failures)}\n")
print(f"{'NAME':30s} {'PI_LEN':>7s} {'SI_LEN':>7s} {'FIRST_DIFF':>10s} {'TYPE':<30s} DETAIL")
print('-' * 130)

categories = {}

for name in failures:
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = get_instrs(pc)
    si = get_instrs(sc)

    first_diff = None
    for i in range(max(len(pi), len(si))):
        a = pi[i] if i < len(pi) else None
        b = si[i] if i < len(si) else None
        if not (a and b and a[1] == b[1] and a[2] == b[2]):
            first_diff = i
            break

    if first_diff is None:
        print(f"{name:30s} {len(pi):7d} {len(si):7d} {'NONE':>10s} {'IDENTICAL':<30s}")
        continue

    a = pi[first_diff] if first_diff < len(pi) else None
    b = si[first_diff] if first_diff < len(si) else None

    diff_type = "unknown"
    detail = ""
    if a and b:
        if a[1] == b[1]:
            # Same op
            if 'JUMP' in a[1] or 'FOR_ITER' in a[1]:
                # Jump target diff
                try:
                    target_diff = (b[2] or 0) - (a[2] or 0) if isinstance(a[2], int) and isinstance(b[2], int) else '?'
                    diff_type = "jump_target_diff"
                    detail = f"op={a[1]} p_tgt={a[2]} s_tgt={b[2]} diff={target_diff}"
                except:
                    diff_type = "jump_target_diff"
                    detail = f"op={a[1]} p={a[2]} s={b[2]}"
            else:
                diff_type = "argval_diff"
                detail = f"op={a[1]} p={a[2]!r} s={b[2]!r}"
        else:
            diff_type = "opname_diff"
            detail = f"p={a[1]}({a[3]}) s={b[1]}({b[3]})"
    elif a and not b:
        diff_type = "src_missing_instr"
        detail = f"p has {a[1]}({a[3]}) but src ended"
    elif b and not a:
        diff_type = "src_extra_instr"
        detail = f"src has {b[1]}({b[3]}) but pyc ended"

    categories.setdefault(diff_type, []).append(name)
    print(f"{name:30s} {len(pi):7d} {len(si):7d} {first_diff:10d} {diff_type:<30s} {detail}")

print("\n=== Categories summary ===")
for cat, names in sorted(categories.items()):
    print(f"{cat}: {len(names)} - {names}")
