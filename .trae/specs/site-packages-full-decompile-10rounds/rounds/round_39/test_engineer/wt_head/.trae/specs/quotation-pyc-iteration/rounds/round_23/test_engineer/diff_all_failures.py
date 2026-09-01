"""R23-N10: 分析所有失败函数的字节码差异，找出可批量修复的模式"""
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
    """返回差异列表：[(idx, p, s)]"""
    diffs = []
    n = max(len(pi), len(si))
    for i in range(n):
        p = pi[i] if i < len(pi) else None
        s = si[i] if i < len(si) else None
        if p == s:
            continue
        # 比较opname+argval
        if p and s and p[1] == s[1] and p[2] == s[2]:
            continue
        diffs.append((i, p, s))
    return diffs


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    with open('/tmp/r23_failures.txt', 'r', encoding='utf-8') as f:
        failures = [l.strip() for l in f if l.strip()]

    # 分类差异模式
    pattern_counts = {}
    detail_per_func = {}

    for name in failures:
        pc = pyc_codes[name]
        sc = src_codes[name]
        pi = get_instr_list(pc)
        si = get_instr_list(sc)
        diffs = diff_instrs(pi, si)

        # 简化差异描述
        sig_diff = []
        if pc.co_argcount != sc.co_argcount:
            sig_diff.append(f"argcount:{pc.co_argcount}!={sc.co_argcount}")
        if pc.co_kwonlyargcount != sc.co_kwonlyargcount:
            sig_diff.append(f"kwonly:{pc.co_kwonlyargcount}!={sc.co_kwonlyargcount}")
        if pc.co_flags != sc.co_flags:
            sig_diff.append(f"flags:{pc.co_flags}!={sc.co_flags}")
        if pc.co_varnames != sc.co_varnames:
            sig_diff.append("varnames_diff")
        if pc.co_freevars != sc.co_freevars:
            sig_diff.append("freevars_diff")
        if pc.co_cellvars != sc.co_cellvars:
            sig_diff.append("cellvars_diff")
        if pc.co_names != sc.co_names:
            sig_diff.append(f"names:{pc.co_names}!={sc.co_names}")

        # 取前5个差异
        first_diffs = diffs[:5]
        detail = []
        for idx, p, s in first_diffs:
            pdesc = f"{p[1]}({p[2]!r})" if p else "None"
            sdesc = f"{s[1]}({s[2]!r})" if s else "None"
            detail.append(f"@{idx}: pyc={pdesc} src={sdesc}")

        detail_per_func[name] = {
            'len_pyc': len(pi),
            'len_src': len(si),
            'n_diffs': len(diffs),
            'first_diffs': detail,
            'sig_diff': sig_diff,
        }

        # 模式分类
        if len(pi) != len(si):
            pattern = f"len_diff (pyc={len(pi)} src={len(si)})"
        elif sig_diff:
            pattern = "sig_only"
        else:
            # 同长度但内容不同
            opnames_diff = set()
            for idx, p, s in diffs:
                if p and s:
                    opnames_diff.add(f"{p[1]}->{s[1]}")
            pattern = f"opname: {','.join(sorted(opnames_diff)[:3])}"

        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

    print("=== 失败模式分类 ===")
    for p, c in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        print(f"  [{c}] {p}")

    print("\n=== 各函数详细差异 (前5) ===")
    for name in failures:
        info = detail_per_func[name]
        print(f"\n--- {name} (pyc={info['len_pyc']} src={info['len_src']} diffs={info['n_diffs']}) ---")
        if info['sig_diff']:
            print(f"  SIG: {info['sig_diff']}")
        for d in info['first_diffs']:
            print(f"  {d}")


if __name__ == '__main__':
    main()
