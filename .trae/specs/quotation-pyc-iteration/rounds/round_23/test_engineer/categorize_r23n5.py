"""R23-N5: 用精确比较逻辑分类失败函数"""
import sys
import dis
import types
import collections

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
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def instr_equal(a, b):
    if a[1] != b[1]:
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
        if av_a.co_name != av_b.co_name: return False
        if av_a.co_varnames != av_b.co_varnames: return False
        if av_a.co_freevars != av_b.co_freevars: return False
        if av_a.co_cellvars != av_b.co_cellvars: return False
        if av_a.co_argcount != av_b.co_argcount: return False
        if av_a.co_kwonlyargcount != av_b.co_kwonlyargcount: return False
        if av_a.co_flags != av_b.co_flags: return False
        return True
    return av_a == av_b


def first_diff_recursive(co_a, co_b, path):
    """递归找首个差异"""
    pi = get_instr_list(co_a)
    si = get_instr_list(co_b)
    if len(pi) != len(si):
        for i in range(min(len(pi), len(si))):
            if pi[i][1] != si[i][1]:
                return f"opname_diff@{pi[i][0]} pyc={pi[i][1]}({pi[i][2]!r}) src={si[i][1]}({si[i][2]!r}) [path={path}]"
        return f"length_diff@offset_{pi[min(len(pi), len(si))-1][0] if pi else -1} pyc={len(pi)} src={len(si)} [path={path}]"
    for i, (a, b) in enumerate(zip(pi, si)):
        if a[1] != b[1]:
            return f"opname_diff@{a[0]} pyc={a[1]}({a[2]!r}) src={b[1]}({b[2]!r}) [path={path}]"
        av_a, av_b = a[2], b[2]
        if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
            sub = first_diff_recursive(av_a, av_b, f"{path}.{av_a.co_name}")
            if sub:
                return sub
            if av_a.co_name != av_b.co_name:
                return f"codename@{a[0]} pyc={av_a.co_name!r} src={av_b.co_name!r} [path={path}]"
            if av_a.co_varnames != av_b.co_varnames:
                return f"varnames@{a[0]} pyc={av_a.co_varnames} src={av_b.co_varnames} [path={path}]"
            if av_a.co_freevars != av_b.co_freevars:
                return f"freevars@{a[0]} pyc={av_a.co_freevars} src={av_b.co_freevars} [path={path}]"
            if av_a.co_cellvars != av_b.co_cellvars:
                return f"cellvars@{a[0]} pyc={av_a.co_cellvars} src={av_b.co_cellvars} [path={path}]"
            if av_a.co_argcount != av_b.co_argcount:
                return f"argcount@{a[0]} pyc={av_a.co_argcount} src={av_b.co_argcount} [path={path}]"
            if av_a.co_kwonlyargcount != av_b.co_kwonlyargcount:
                return f"kwonlyargcount@{a[0]} [path={path}]"
            if av_a.co_flags != av_b.co_flags:
                return f"flags@{a[0]} pyc={av_a.co_flags} src={av_b.co_flags} [path={path}]"
            continue
        if av_a != av_b:
            return f"argval_diff@{a[0]} op={a[1]} pyc={av_a!r} src={av_b!r} [path={path}]"
    return None


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    with open('/tmp/r23_failures.txt', 'r') as f:
        failures = [l.strip() for l in f if l.strip()]

    print(f"=== R23-N6 失败函数 ({len(failures)}) 分类 ===\n")

    categories = collections.Counter()
    details = []
    for name in failures:
        pc = pyc_codes[name]
        sc = src_codes[name]
        diff = first_diff_recursive(pc, sc, name)
        if diff is None:
            if pc.co_argcount != sc.co_argcount: diff = f"sig_argcount pyc={pc.co_argcount} src={sc.co_argcount}"
            elif pc.co_kwonlyargcount != sc.co_kwonlyargcount: diff = f"sig_kwonlyargcount"
            elif pc.co_posonlyargcount != sc.co_posonlyargcount: diff = f"sig_posonlyargcount pyc={pc.co_posonlyargcount} src={sc.co_posonlyargcount}"
            elif pc.co_flags != sc.co_flags: diff = f"sig_flags pyc={pc.co_flags:#x} src={sc.co_flags:#x}"
            elif pc.co_varnames != sc.co_varnames: diff = f"sig_varnames pyc={pc.co_varnames} src={sc.co_varnames}"
            elif pc.co_freevars != sc.co_freevars: diff = f"sig_freevars"
            elif pc.co_cellvars != sc.co_cellvars: diff = f"sig_cellvars"
            elif pc.co_names != sc.co_names: diff = f"sig_names pyc={pc.co_names} src={sc.co_names}"
            else: diff = "UNKNOWN"

        if diff.startswith("opname_diff"):
            cat = "opname_diff"
        elif diff.startswith("length_diff"):
            cat = "length_diff"
        elif diff.startswith("argval_diff"):
            cat = "argval_diff"
        elif diff.startswith("sig_"):
            cat = "sig_diff"
        elif diff.startswith("varnames") or diff.startswith("codename") or diff.startswith("flags") or diff.startswith("argcount") or diff.startswith("kwonlyargcount") or diff.startswith("freevars") or diff.startswith("cellvars"):
            cat = "code_obj_meta"
        else:
            cat = "unknown"
        categories[cat] += 1
        details.append((name, cat, diff))

    for cat, cnt in categories.most_common():
        print(f"  {cat}: {cnt}")

    print("\n--- 详细列表 ---")
    for cat, _ in categories.most_common():
        print(f"\n## {cat}")
        for name, c, diff in details:
            if c == cat:
                print(f"  {name}: {diff}")


if __name__ == '__main__':
    main()
