"""R24 严格字节码一致性统计（L1 口径）。

评估结论：当前归一化口径（exact_match_stats.py）的 4 项豁免中，
elif 链等价 / 常量 set-tuple 等价 / module 委托比较 均为冗余容错，
反编译器已能完全复现原始字节码布局。本脚本收紧为 L1 口径：

L1 仅保留 2 项【永远合理】的豁免：
  1. 跳过 CACHE / NOP / EXTENDED_ARG —— CPython 解释器对齐填充，
     重新编译会自动重新生成，与源码语义无关。
  2. code object 递归比较指令序列，忽略 co_filename / co_firstlineno /
     运行时内存地址 —— 这些是反编译器无法恢复的元数据
     （原始源文件路径、行号布局、对象地址）。

去掉的冗余豁免（L1 不使用仍达 100%，证明反编译器输出布局完全复现）：
  - elif 链跳转目标等价（_jump_targets_equiv / _chase_elif_chain）
  - 常量 set/tuple 等价（_const_equiv）
  - module 委托比较（_compare_module_with_delegation）—— 被 code 递归取代

判定：跳转目标按绝对 offset 严格比较，常量按 == 严格比较。
"""
import sys, types, dis, os, json

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
DECOMPILED = '/tmp/r24_decompiled.py'
OUT_DIR = '/tmp/r24_strict_out'
OUT_JSON = OUT_DIR + '/bc_results.json'

# 唯一保留的豁免：CPython 解释器对齐填充指令
SKIP_OPS = frozenset(['CACHE', 'NOP', 'EXTENDED_ARG'])


def get_instr_list(co):
    """返回指令列表；code object 递归为指令序列（忽略元数据），标记为 ('CODE', name, sub_instrs)。

    忽略的元数据：co_filename（原始源路径，反编译器无法恢复）、
    co_firstlineno（行号布局，反编译产物必然不同）、运行时对象地址。
    递归比较 co_consts 中的嵌套 code object 的指令序列，确保嵌套函数语义一致。
    """
    out = []
    for ins in dis.get_instructions(co):
        if ins.opname in SKIP_OPS:
            continue
        av = ins.argval
        if isinstance(av, types.CodeType):
            out.append(('CODE', av.co_name, get_instr_list(av)))
        else:
            out.append((ins.opname, av))
    return out


def walk_code(co, prefix='', sink=None):
    if sink is None:
        sink = {}
    name = '<module>' if (co.co_name == '<module>' and not prefix) else prefix + co.co_name
    sink[name] = co
    sub_prefix = '' if name == '<module>' else name + '.'
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            walk_code(const, sub_prefix, sink)
    return sink


def load_orig():
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    return code_obj


def compare_one(orig_co, new_co):
    oa = get_instr_list(orig_co)
    na = get_instr_list(new_co)
    if len(oa) != len(na):
        return {'status': 'len_diff', 'orig_len': len(oa), 'new_len': len(na),
                'diff': len(na) - len(oa)}
    first_diff = -1
    for i, (x, y) in enumerate(zip(oa, na)):
        if x != y:
            first_diff = i
            break
    if first_diff < 0:
        return {'status': 'match'}
    return {'status': 'instr_diff', 'first_diff_idx': first_diff,
            'orig_at': list(oa[first_diff]), 'new_at': list(na[first_diff])}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    orig_top = load_orig()
    orig_cos = walk_code(orig_top)
    print(f"[strict] orig code objects: {len(orig_cos)}")

    with open(DECOMPILED, 'r', encoding='utf-8') as f:
        src = f.read()
    try:
        new_code = compile(src, '<decompiled>', 'exec')
        compile_ok = True
    except SyntaxError as e:
        new_code = None
        compile_ok = False
        print(f"[strict] compile FAILED: {e}")

    new_cos = walk_code(new_code) if new_code is not None else {}
    print(f"[strict] new code objects: {len(new_cos)}")

    results = {}
    matched = mismatched = missing = 0
    for name, orig_co in orig_cos.items():
        if name not in new_cos:
            results[name] = {'status': 'missing'}
            missing += 1
            continue
        r = compare_one(orig_cos[name], new_cos[name])
        results[name] = r
        if r['status'] == 'match':
            matched += 1
        else:
            mismatched += 1

    total = len(orig_cos)
    sr = matched / total * 100 if total else 0.0
    print(f"[strict] compile_ok={compile_ok}")
    print(f"[strict] total={total} matched={matched} mismatched={mismatched} "
          f"missing={missing} success_rate={sr:.2f}%")
    print(f"[strict] L1 口径(仅跳过 CACHE/NOP/EXTENDED_ARG + code 递归忽略元数据)")

    out = {'summary': {'total': total, 'matched': matched, 'mismatched': mismatched,
                       'missing': missing, 'success_rate_pct': round(sr, 2),
                       'compile_ok': compile_ok, 'level': 'L1'},
           'results': results}
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, default=str)
    print(f"[strict] wrote {OUT_JSON}")

    mism = [(n, r) for n, r in results.items() if r['status'] != 'match']
    if mism:
        print(f"[strict] mismatched functions ({len(mism)}):")
        for n, r in mism:
            if r['status'] == 'len_diff':
                print(f"  - {n}: len_diff {r['orig_len']}->{r['new_len']} ({r['diff']:+d})")
            elif r['status'] == 'instr_diff':
                print(f"  - {n}: instr_diff@{r['first_diff_idx']}")
            else:
                print(f"  - {n}: {r['status']}")
    else:
        print(f"[strict] 0 mismatched — 字节码布局完全复现 (跳转目标按绝对offset严格比较)")


if __name__ == '__main__':
    main()
