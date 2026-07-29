"""R23-N11: 找出最简单的失败函数（按diff数量排序）"""
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


def get_instr_list(co):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname == 'EXTENDED_ARG':
            continue
        if ins.opname == 'CACHE':
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def diff_instrs(pi, si):
    diffs = []
    n = max(len(pi), len(si))
    for i in range(n):
        p = pi[i] if i < len(pi) else None
        s = si[i] if i < len(si) else None
        if p is None or s is None:
            diffs.append((i, p, s))
            continue
        if p[1] != s[1]:
            diffs.append((i, p, s))
            continue
        av_a, av_b = p[2], s[2]
        if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
            if av_a.co_name != av_b.co_name:
                diffs.append((i, p, s))
            continue
        if av_a != av_b:
            diffs.append((i, p, s))
    return diffs


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    with open('/tmp/r23_failures.txt', 'r', encoding='utf-8') as f:
        failures = [l.strip() for l in f if l.strip()]

    results = []
    for name in failures:
        pc = pyc_codes[name]
        sc = src_codes[name]
        pi = get_instr_list(pc)
        si = get_instr_list(sc)
        diffs = diff_instrs(pi, si)
        results.append((name, len(diffs), len(pi), len(si), diffs))

    results.sort(key=lambda x: x[1])

    print("=== 失败函数按 diff 数量排序（最少在前）===")
    for name, n_diffs, len_p, len_s, diffs in results[:15]:
        print(f"\n--- {name} (diffs={n_diffs}, pyc_len={len_p}, src_len={len_s}) ---")
        # Check sig diff
        pc = pyc_codes[name]
        sc = src_codes[name]
        sig_diff = []
        if pc.co_argcount != sc.co_argcount:
            sig_diff.append(f"argcount:{pc.co_argcount}!={sc.co_argcount}")
        if pc.co_flags != sc.co_flags:
            sig_diff.append(f"flags:{pc.co_flags}!={sc.co_flags}")
        if pc.co_varnames != sc.co_varnames:
            sig_diff.append("varnames_diff")
        if pc.co_names != sc.co_names:
            sig_diff.append("names_diff")
        if sig_diff:
            print(f"  SIG: {sig_diff}")
        # Show first 8 diffs
        for idx, p, s in diffs[:8]:
            pdesc = f"{p[1]}({p[2]!r})" if p else "None"
            sdesc = f"{s[1]}({s[2]!r})" if s else "None"
            print(f"  @{idx}: pyc={pdesc} src={sdesc}")


if __name__ == '__main__':
    main()
