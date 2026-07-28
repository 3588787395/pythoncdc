"""R24 测试工程师：分类20个失败函数的失败模式"""
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
    return [(ins.offset, ins.opname, ins.argval, getattr(ins, 'argrepr', '')) for ins in dis.get_instructions(co) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    with open('/tmp/r23_failures.txt', 'r', encoding='utf-8') as f:
        failures = [line.strip() for line in f if line.strip()]

    print(f"Total failures: {len(failures)}\n")

    for name in failures:
        pc = pyc_codes[name]
        sc = src_codes[name]
        pi = get_instrs(pc)
        si = get_instrs(sc)

        # Find first diff
        first_diff = None
        for i in range(max(len(pi), len(si))):
            a = pi[i] if i < len(pi) else None
            b = si[i] if i < len(si) else None
            if not (a and b and a[1] == b[1] and a[2] == b[2]):
                first_diff = i
                break

        if first_diff is None:
            print(f"=== {name} === IDENTICAL")
            continue

        a = pi[first_diff] if first_diff < len(pi) else None
        b = si[first_diff] if first_diff < len(si) else None

        # Categorize
        diff_type = "unknown"
        detail = ""
        if a and b:
            if a[1] == b[1]:
                if 'JUMP' in a[1] or 'FOR_ITER' in a[1]:
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

        # Get context
        start = max(0, first_diff - 3)
        end = min(max(len(pi), len(si)), first_diff + 3)
        ctx_p = []
        ctx_s = []
        for i in range(start, end):
            pa = pi[i] if i < len(pi) else None
            sa = si[i] if i < len(si) else None
            ctx_p.append(f"{pa[1]}({pa[3]})" if pa else "(none)")
            ctx_s.append(f"{sa[1]}({sa[3]})" if sa else "(none)")

        print(f"=== {name} ===")
        print(f"  pyc: {len(pi)} instrs, src: {len(si)} instrs, first_diff: {first_diff}")
        print(f"  type: {diff_type}")
        print(f"  detail: {detail}")
        print(f"  pyc ctx: {' | '.join(ctx_p)}")
        print(f"  src ctx: {' | '.join(ctx_s)}")
        print()


if __name__ == '__main__':
    main()
