"""R26 测试工程师：分类失败函数，识别共性问题类型"""
import sys
import types
import dis

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r26_decompiled.py'


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
    out = []
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        out.append((ins.offset, ins.opname, ins.argval, ins.argrepr))
    return out


def categorize():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    with open('/tmp/r26_failures.txt') as f:
        failures = [l.strip() for l in f if l.strip()]

    counts = {}
    details = {}
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
            counts['IDENTICAL'] = counts.get('IDENTICAL', 0) + 1
            details[name] = ('IDENTICAL', '')
            continue
        a = pi[first_diff] if first_diff < len(pi) else None
        b = si[first_diff] if first_diff < len(si) else None
        diff_type = "unknown"
        detail = ""
        if a and b:
            if a[1] == b[1]:
                if 'JUMP' in a[1] or 'FOR_ITER' in a[1] or 'SETUP' in a[1]:
                    diff_type = "jump_target_diff"
                    try:
                        td = (b[2] or 0) - (a[2] or 0) if isinstance(a[2], int) and isinstance(b[2], int) else 0
                        detail = f"op={a[1]} pyc_tgt={a[2]} src_tgt={b[2]} diff={td:+d}"
                    except Exception:
                        detail = f"op={a[1]} p={a[2]!r} s={b[2]!r}"
                else:
                    diff_type = "argval_diff"
                    detail = f"op={a[1]} p={a[2]!r} s={b[2]!r}"
            else:
                diff_type = "opname_diff"
                detail = f"pyc={a[1]}({a[3]}) src={b[1]}({b[3]})"
        elif a and not b:
            diff_type = "src_missing_instr"
            detail = f"pyc has {a[1]}({a[3]}) at idx {first_diff} (pyc_len={len(pi)}, src_len={len(si)})"
        elif b and not a:
            diff_type = "src_extra_instr"
            detail = f"src has {b[1]}({b[3]}) at idx {first_diff} (pyc_len={len(pi)}, src_len={len(si)})"
        counts[diff_type] = counts.get(diff_type, 0) + 1
        details[name] = (diff_type, detail)

    print("=== 失败类型统计 ===")
    for t, c in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")

    print("\n=== 各函数首处差异 ===")
    for name in failures:
        t, d = details[name]
        print(f"  {name}: [{t}] {d}")


if __name__ == '__main__':
    categorize()
